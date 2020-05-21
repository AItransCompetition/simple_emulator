#!/usr/bin/python
# -*- coding: utf-8 -*-


from objects.pcc_emulator import PccEmulator
import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config import constant

from qoe_difference import cal_distance, plt_qoe

if __name__ == '__main__':

    block_file = "config/block.txt"
    trace_file = "config/trace.txt"
    new_trace_file = "scripts/first_group/traces_51.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"
    pic = "qoemodel/qoes_buffer.png"
    idx, size = "queue_size", 50
    x = 0.9
    reno_arr = []
    bbr_arr = []
    for j in range(10, 60):
        constant.MAX_QUEUE = constant.MIN_QUEUE = j
        qoe_difference = cal_distance(block_file, trace_file, x)
        reno_arr.append(qoe_difference[0])
        bbr_arr.append(qoe_difference[1])

    plt_qoe(reno_arr, bbr_arr, pic, idx, size)

    with open("qoemodel/qoes_buffer.log","w+") as f:
        strs = ["buffer: MAX_QUEUE = 10, MIN_QUEUE = 59\n",
                "qoe = 0.9 * priority + 0.1 * deadline\n",
                str(reno_arr) + "\n",
                str(bbr_arr)]
        f.writelines(strs)







