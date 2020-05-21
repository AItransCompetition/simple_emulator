from config.constant import *
from utils import debug_print
from objects.cc_base import CongestionControl


class MTR(CongestionControl):

    def __init__(self):
        super(MTR, self).__init__()
        self.trace_list = []
        self.USE_CWND = False

    def init_trace(self, trace_file):
        with open(trace_file, 'r') as f:
            for line in f.readlines():
                self.trace_list.append(list(
                    map(lambda x: float(x), line.split(","))
                ))
        self.send_rate = self.trace_list[0][1] * 10**6 / BYTES_PER_PACKET /2

    def update_trace(self, cur_time):
        for i in range(len(self.trace_list)):
            if self.trace_list[i][0] >= cur_time:
                break
            self.send_rate = self.trace_list[i][1] * 10**6 / BYTES_PER_PACKET /2

    def make_decision(self, cur_time):
        self.update_trace(cur_time)
        output = {
            "send_rate" : self.send_rate
        }
        return output

    def cc_trigger(self, data):
        event_time = data["event_time"]
        self.update_trace(event_time)

    def append_input(self, data):
        self._input_list.append(data)

        if data["event_type"] != PACKET_TYPE_TEMP:
            self.cc_trigger(data)
            return {
                "send_rate" : self.send_rate
            }
        return None

