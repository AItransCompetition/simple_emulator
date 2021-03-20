import heapq, random, json
from config.constant import *
from utils import get_packet_type, get_emulator_info, debug_print
from config import constant


class Engine():

    def __init__(self, senders, links, **kwargs):
        self.update_config(kwargs)
        self.q = []
        self.cur_time = 0.0
        self.senders = senders
        self.links = links
        self.queue_initial_packets()

        self.log_packet_file = "output/packet_log/packet-0.log"
        self.log_items = 0
        self.last_alert_time = 0
        self.tmp_log = []

    def update_config(self, extra):
        self.run_dir = extra["RUN_DIR"]+'/' if "RUN_DIR" in extra else ''

    def queue_initial_packets(self):
        """initial the packet queue in network"""
        for sender in self.senders:
            sender.register_network(self)
            sender.reset_obs()
            packet = sender.select_packet(1.0 / sender.rate) # sender.new_packet(1.0 / sender.rate)
            if packet:
                sender.in_event_nums += 1
                heapq.heappush(self.q, (max(1.0 / sender.rate, packet.create_time), sender, packet))

    def reset(self):
        self.cur_time = 0.0
        self.q = []
        [link.reset() for link in self.links]
        [sender.reset() for sender in self.senders]
        self.queue_initial_packets()

    def get_cur_time(self):
        return self.cur_time

    def run_for_dur(self, dur):
        """run the system for time of "dur". """
        end_time = self.cur_time + dur
        for sender in self.senders:
            sender.reset_obs()

        while self.cur_time < end_time:
            if len(self.q) == 0:
                print("Time {}s : There is no packet from application~".format(self.cur_time))
                break

            event_time, sender, packet = heapq.heappop(self.q)
            self.log_packet(event_time, sender, packet)

            event_type, next_hop, cur_latency, dropped, packet_id = packet.parse()
            # print("Got event %s, to link %d, latency %f at time %f" % (event_type, next_hop, cur_latency, event_time))
            self.cur_time = event_time
            new_event_time = event_time
            new_event_type = event_type
            new_next_hop = next_hop
            new_latency = cur_latency
            new_dropped = dropped
            push_new_event = False

            if event_type == EVENT_TYPE_ACK:
                # got ack in source or destination
                if next_hop == len(sender.path):
                    packet.finish_time = event_time
                    self.append_cc_input(event_time, sender, packet)
                    sender.in_event_nums -= 1
                    if dropped:
                        sender.on_packet_lost(event_time, packet)
                        # print("Packet lost at time %f" % self.cur_time)
                    else:
                        # may acked packet which is not in window after packet loss
                        sender.on_packet_acked(packet.get_rtt(), packet, event_time)
                    # for windows-based cc
                    if sender.USE_CWND:
                        # continue ack may use same inflight numbers which will be limited to cwnd but redundancy in log
                        for _packet in sender.slide_windows(self.cur_time, sender.in_event_nums):
                            sender.in_event_nums += 1
                            heapq.heappush(self.q, (max(self.cur_time+(1.0 / sender.rate), _packet.create_time), \
                                                sender, _packet))

                # ack back to source
                else:
                    new_next_hop = next_hop + 1
                    link_latency = sender.path[next_hop].get_cur_latency(self.cur_time)
                    if USE_LATENCY_NOISE:
                        link_latency *= random.uniform(1.0, MAX_LATENCY_NOISE)
                    new_latency += link_latency
                    new_event_time += link_latency
                    push_new_event = True
            if event_type == EVENT_TYPE_SEND:
                if next_hop == 0:
                    # print("Packet sent at time %f" % self.cur_time)
                    if sender.can_send_packet(new_event_time):
                        pacing_time, extra_info = sender.on_packet_sent(new_event_time)
                        packet.pacing_delay += pacing_time
                        packet.extra = extra_info
                        push_new_event = True
                    else:
                        sender.in_event_nums -= 1
                        if sender.application:
                            sender.wait_for_push_packets.append([event_time, sender, packet])
                    # when do the packet create ? before or after pacing ?
                    _packet = sender.select_packet(new_event_time + (1.0 / sender.rate)) # new_packet(new_event_time + (1.0 / sender.rate))
                    if _packet:
                        heapq.heappush(sender.wait_for_push_packets, [_packet.create_time, sender, _packet])
                        if not sender.USE_CWND or int(sender.cwnd) > sender.in_event_nums:
                            item = heapq.heappop(sender.wait_for_push_packets)
                            sender.in_event_nums += 1
                            heapq.heappush(self.q, (max(new_event_time + (1.0 / sender.rate), item[0]), item[1], item[2]))
                    new_event_time += pacing_time
                else:
                    push_new_event = True

                if next_hop == sender.dest:
                    new_event_type = EVENT_TYPE_ACK
                new_next_hop = next_hop + 1
                link_latency = sender.path[next_hop].get_cur_latency(new_event_time)
                if USE_LATENCY_NOISE:
                    link_latency *= random.uniform(1.0, MAX_LATENCY_NOISE)
                new_latency += link_latency
                new_dropped = not sender.path[next_hop].packet_enters_link(new_event_time)
                new_event_time += link_latency

            if push_new_event:
                packet.next_hop = new_next_hop
                packet.packet_type = new_event_type
                packet.latency = new_latency
                packet.drop = new_dropped
                heapq.heappush(self.q, (new_event_time, sender, packet))
        self.close()
        sender_mi = self.senders[0].get_run_data()
        throughput = sender_mi.get("recv rate")
        latency = sender_mi.get("avg latency")
        loss = sender_mi.get("loss ratio")
        # bw_cutoff = self.links[0].bw * 0.8
        # lat_cutoff = 2.0 * self.links[0].dl * 1.5
        # loss_cutoff = 2.0 * self.links[0].lr * 1.5
        # print("thpt %f, bw %f" % (throughput, bw_cutoff))
        # reward = 0 if (loss > 0.1 or throughput < bw_cutoff or latency > lat_cutoff or loss > loss_cutoff) else 1 #

        # Super high throughput
        # reward = REWARD_SCALE * (20.0 * throughput / RATE_OBS_SCALE - 1e3 * latency / LAT_OBS_SCALE - 2e3 * loss)

        # Very high thpt
        reward = (10.0 * throughput / (8 * BYTES_PER_PACKET) - 1e3 * latency - 2e3 * loss)

        # High thpt
        # reward = REWARD_SCALE * (5.0 * throughput / RATE_OBS_SCALE - 1e3 * latency / LAT_OBS_SCALE - 2e3 * loss)

        # Low latency
        # reward = REWARD_SCALE * (2.0 * throughput / RATE_OBS_SCALE - 1e3 * latency / LAT_OBS_SCALE - 2e3 * loss)
        # if reward > 857:
        # print("Reward = %f, thpt = %f, lat = %f, loss = %f" % (reward, throughput, latency, loss))

        # reward = (throughput / RATE_OBS_SCALE) * np.exp(-1 * (LATENCY_PENALTY * latency / LAT_OBS_SCALE + LOSS_PENALTY * loss))
        return reward * REWARD_SCALE

    def get_true_log_file(self):
        """if the rows of single log file is limited to MAX_PACKET_LOG_ROWS, find the name of next new log file."""
        if isinstance(constant.MAX_PACKET_LOG_ROWS, int) and constant.MAX_PACKET_LOG_ROWS > 0:
            file_nums = self.log_items
            self.log_items += 1
            return self.run_dir + self.log_packet_file.replace('0', str(file_nums))

    def log_packet(self, event_time, sender, packet):
        """
        log the event information.
        :param event_time: the time happened this event.
        :param sender: the sender sent this packet.
        :param packet: type Packet.
        """
        # only log the first sender when ENABLE_LOG=True
        if not constant.ENABLE_LOG:
            return packet

        if constant.ENABLE_DEBUG and event_time - self.last_alert_time >= ALERT_CIRCLE:
            self.last_alert_time = event_time
            sender_mi = self.senders[0].get_run_data()
            print("Time : {}".format(event_time))
            print(get_emulator_info(sender_mi))

        log_data = {
            "Time" : event_time,
            "Waiting_for_ack_nums" : sender.get_waiting_ack_nums(),
            "Sender_id" : sender.id
        }
        log_data.update(packet.trans2dict())
        if sender.USE_CWND:
            log_data["Extra"]["Cwnd"] = sender.cwnd
        if sender.rate != float("inf"):
            log_data["Extra"]["Send_rate"] = sender.rate
        # log_data["Extra"]["in_event_nums"] = sender.in_event_nums
        # log_data["Extra"]["wait_for_select"] = len(sender.wait_for_select_packets)
        # log_data["Extra"]["wait_for_push"] = len(sender.wait_for_push_packets)
        self.tmp_log.append(log_data)
        if len(self.tmp_log) % constant.MAX_PACKET_LOG_ROWS == 0:
            self.flush_log()
        return packet

    def flush_log(self):
        with open(self.get_true_log_file(), "w") as f:
            for item in self.tmp_log:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.tmp_log = []

    def append_cc_input(self, event_time, sender, packet, event_type="packet"):
        """push the acked or lost packet event to it's sender"""
        # only use the solution's sender
        if sender.id != self.senders[0].id:
            return
        if event_type == "packet":
            event_info = {
                "event_type" : get_packet_type(sender, packet),
                "packet_information_dict" : packet.trans2dict()
            }
            event_info["packet_information_dict"]["Extra"]["inflight"] = sender.get_waiting_ack_nums()
        # todo : how to design system information
        elif event_type == "system":
            event_info = {

            }

        feed_back = sender.solution.cc_trigger(event_time, event_info)
        # clear memory from solution._input_list
        if hasattr(sender.solution, "_input_list") and len(sender.solution._input_list) > 10000:
            sender.solution._input_list = sender.solution._input_list[5000:]
        if feed_back:
            sender.cwnd = feed_back["cwnd"] if "cwnd" in feed_back else sender.cwnd
            sender.rate = feed_back["send_rate"] if "send_rate" in feed_back else sender.rate
            sender.pacing_rate = feed_back["pacing_rate"] if "pacing_rate" in feed_back else sender.pacing_rate

    def close(self):
        """close all the application before closing this system."""
        self.flush_log()
        for sender in self.senders:
            debug_print("sender {} wait_for_push_packets size {}".format(sender.id, len(sender.wait_for_push_packets)))
            if sender.application:
                sender.application.close(self.cur_time)