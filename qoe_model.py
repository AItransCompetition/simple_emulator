#!/usr/bin/python
# -*- coding: utf-8 -*-


from objects.emulator import PccEmulator
import os, sys, inspect
from config.constant import *
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import json, shutil

from player.aitrans_solution import Solution as s1


def cal_qoe(x=0.9):
    block_data = []
    urgency = []
    priorities = []
    qoe = 0
    tmp = [3, 2, 1]
    with open("output/block.log", "r") as f:
        for line in f.readlines():
            data = json.loads(line.replace("'", '"'))
            # not finished
            if data["Miss_ddl"] == 0 and data["Size"] - data["Finished_bytes"] > 0.000001:
                continue
            block_data.append(data)
    for block in block_data:
        priority = float(tmp[int(block['Priority'])] / 3)
        priorities.append(priority)
        if block["Miss_ddl"] == 0:
            urgency.append(1)
        else:
            urgency.append(0)
            priorities[-1] *= 0
    for i in range(len(urgency)):
        qoe += x * priorities[i] + (1 - x) * urgency[i]
    return qoe

