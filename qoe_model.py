#!/usr/bin/python
# -*- coding: utf-8 -*-


from objects.pcc_emulator import PccEmulator
import os, sys, inspect
from config.constant import *
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import json

from player.aitrans_solution import Solution as s1
from player.aitrans_solution2 import Solution as s2

def cal_qoe(x=0.82):
    block_data = []
    urgency = []
    priorities = []
    qoe = 0
    tmp = [3, 2, 1]
    with open("output/block.log", "r") as f:
        for line in f.readlines():
            block_data.append(json.loads(line.replace("'", '"')))
    for block in block_data:
        priority = float(tmp[int(block['Priority'])] / 3)
        priorities.append(priority)
        if block['Miss_ddl'] == 0:
            urgency.append(1)
        else:
            urgency.append(0)
            priorities[-1] *= -1
    for i in range(len(urgency)):
        qoe += x * priorities[i] + (1 - x) * urgency[i]
    return qoe

def cal_distance(block_file, trace_file, x):
    emulator1 = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=s1()
    )
    emulator1.run_for_dur(float("inf"))
    reno_qoe = cal_qoe(x)

    emulator2 = PccEmulator(
        block_file=block_file,
        trace_file=trace_file,
        queue_range=(MIN_QUEUE, MAX_QUEUE),
        solution=s2()
    )
    emulator2.run_for_dur(float("inf"))
    bbr_qoe = cal_qoe(x)
    return abs(reno_qoe - bbr_qoe)



if __name__ == '__main__':

    block_file = "config/block.txt"
    log_file = "output/pcc_emulator.log"
    log_packet_file = "output/packet_log/packet-0.log"

    x = 0
    qoes = {}
    for i in range(1, 100, 3):
        x = i / 100
        arr = []
        for j in range(1, 101):
            trace_file = "scripts/first_group/traces_" + str(j) + ".txt"
            qoe_distance = cal_distance(block_file, trace_file, x)
            arr.append(qoe_distance)
        arr = np.array(arr, float)
        qoes[x] = np.var(arr)
    best_x = max(qoes, key=qoes.get)
    with open("qoemodel/qoe_model.log","w+") as f:
        f.write(str(qoes) + '\n')
        f.write(str(best_x) + " * priority + " + str(1 - best_x) + " * ddl " )





