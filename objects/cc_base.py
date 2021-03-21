class CongestionControl(object):

    def __init__(self):
        self._input_list = []
        self.cwnd = 1
        self.send_rate = float("inf")
        self.pacing_rate = float("inf")
        self.call_nums = 0
        self.USE_CWND = False

    def on_packet_sent(self, cur_time):
        """call this when sender send packet"""
        self.call_nums += 1

        output = {
            "cwnd" : self.cwnd,
            "send_rate" : self.send_rate,
            "extra" : { }
        }

        return output

    def cc_trigger(self, cur_time, event_info):
        self._input_list.append([cur_time, event_info])

        return None