#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : main
# @Function : 
# @Author : azson
# @Time : 2020/3/2 20:02
'''

from objects.pcc_emulator import PccEmulator
from utils import analyze_pcc_emulator, plot_cwnd, plot_rate
import os, sys, inspect
from config.constant import *

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from player.aitrans_solution import Solution as s1
from player.aitrans_solution2 import Solution as s2
from player.aitrans_3 import Solution as s3


if __name__ == '__main__':

    block_file = "config/block.txt"
    trace_file = "config/trace.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"

    new_trace_file = "scripts/first_group/traces_1.txt"
    new_block_files = ["config/data_video.csv", "config/data_audio.csv"]

    emulator = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE)
    )

    print(emulator.run_for_dur(15))
    emulator.dump_events_to_file(log_file)
    emulator.print_debug()
    print(emulator.senders[0].rtt_samples)
    print(emulator.senders[0].application.ack_blocks)
    analyze_pcc_emulator(log_packet_file, file_range="all")
    plot_cwnd(log_packet_file, trace_file=trace_file, file_range="all")
    # plot_throughput(log_packet_file, trace_file=trace_file, file_range="all")