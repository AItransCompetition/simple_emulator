#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : double_flow
# @Function : 
# @Author : azson
# @Time : 2020/4/10 15:52
'''

from objects.pcc_emulator import PccEmulator
from utils import analyze_pcc_emulator, plot_cwnd, plot_rate
import os, sys, inspect, random
from config.constant import *
from objects.windows_based_sender import Sender as WinSender
from objects.engine import Engine
from objects.link import Link

from player.examples.reno import Reno
# from player.examples.simple_bbr import BBR
from player.examples.match_trace_rate import MTR
from player.packet_selection import Solution as PacketSelection
from objects.cc_base import CongestionControl


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


# class BbrSolution(BBR, PacketSelection):
#     pass


class RenoSolution(Reno, PacketSelection):
    pass


class NormalSolution(MTR, PacketSelection):
    pass
    # def __init__(self):
    #     super().__init__()
    #     self.send_rate = 100
    #     self.USE_CWND = False
    #
    # def make_decision(self, cur_time):
    #     return {
    #         "send_rate": self.send_rate
    #     }


def create_2flow_emulator(solution, block_file=None, trace_file=None, **kwargs):

    emulator = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        senders=[],
        links=[],
        **kwargs
    )
    emulator.trace_list = emulator.get_trace()
    queue = int(random.uniform(*emulator.queue_range))
    emulator.links = [Link(emulator.trace_list, queue), Link([], queue)]

    solution_1 = solution
    sender_1 = WinSender(emulator.links, 0, emulator.features, history_len=emulator.history_len, solution=solution_1)
    sender_1.init_application(emulator.block_file)

    solution_2 = NormalSolution()
    solution_2.init_trace(emulator.trace_file)
    sender_2 = WinSender(emulator.links, 0, emulator.features, history_len=emulator.history_len, solution=solution_2)
    # sender_2.init_application(emulator.block_file, ENABLE_BLOCK_LOG=False)

    emulator.senders = [sender_1, sender_2]
    emulator.net = Engine(emulator.senders, emulator.links)

    return emulator


if __name__ == '__main__':

    block_file = "config/block.txt"
    trace_file = "config/trace.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"

    new_trace_file = "scripts/first_group/traces_81.txt"
    new_block_files = ["config/data_video.csv", "config/data_audio.csv"]

    tmp = NormalSolution()
    tmp.init_trace(new_trace_file)
    emulator = create_2flow_emulator(RenoSolution(), block_file, new_trace_file)

    print(emulator.run_for_dur(20))
    emulator.dump_events_to_file(log_file)
    emulator.print_debug()
    print(emulator.senders[0].application.ack_blocks)
    from qoe_model import cal_qoe
    print(cal_qoe(0.9))
    # analyze_pcc_emulator(log_packet_file, file_range="all")
    # plot_cwnd(log_packet_file, trace_file=trace_file, file_range="all")
    # plot_throughput(log_packet_file, trace_file=trace_file, file_range="all")