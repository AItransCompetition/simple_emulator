class CongestionControl(object):

    def __init__(self):
        self._input_list = []
        self.cwnd = 1
        self.send_rate = float("inf")
        self.pacing_rate = float("inf")
        self.call_nums = 0

    def on_packet_sent(self, cur_time):
        """call this when sender send packet"""
        self.call_nums += 1

        output = {
            "cwnd" : self.cwnd,
            "send_rate" : self.send_rate,
            "extra" : { }
        }

        return output

    def cc_trigger(self, data):
        self._input_list.append(data)

        return None