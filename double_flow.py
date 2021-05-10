#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : double_flow
# @Function : 
# @Author : azson
# @Time : 2020/4/10 15:52
'''

from objects.emulator import SimpleEmulator
from utils import analyze_emulator, plot_cwnd, plot_rate
import os, sys, inspect, random
from config.constant import *
from objects.sender import Sender as WinSender
from objects.engine import Engine
from objects.link import Link

from player.examples.reno import Reno
# from player.examples.simple_bbr import BBR
from player.examples.match_trace_rate import MTR
from player.block_selection import Solution as BlockSelection
from objects.cc_base import CongestionControl


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


class RenoSolution(Reno, BlockSelection):
    pass


class NormalSolution(MTR, BlockSelection):
    pass


# send block if exists
class DirectSendSolution(CongestionControl, BlockSelection):
    pass


def create_2flow_emulator(solution, block_file=None, trace_file=None, **kwargs):
    emulator = SimpleEmulator(
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
    sender_1.init_application(emulator.block_file, **kwargs)

    solution_2 = NormalSolution()
    solution_2.init_trace(emulator.trace_file)
    sender_2 = WinSender(emulator.links, 0, emulator.features, history_len=emulator.history_len, solution=solution_2)
    # sender_2.init_application(emulator.block_file, ENABLE_BLOCK_LOG=False)

    emulator.senders = [sender_1, sender_2]
    emulator.net = Engine(emulator.senders, emulator.links, **kwargs)

    return emulator


def create_multi_service_emulator(solution_list, sender_block_file_list, trace_file, **kwargs):
    # create normal emulator
    emulator = SimpleEmulator(
        block_file=sender_block_file_list[0],
        trace_file=trace_file,
        senders=[],
        links=[],
        **kwargs
    )
    # reset links of emulator
    emulator.trace_list = emulator.get_trace()
    queue = int(random.uniform(*emulator.queue_range))
    emulator.links = [Link(emulator.trace_list, queue), Link([], queue, delay=emulator.trace_list[0][3])]

    # reset senders of emulator
    senders = []
    for idx, solution in enumerate(solution_list):
        solution = solution if solution else DirectSendSolution()
        sender = WinSender(emulator.links, 0, emulator.features, history_len=emulator.history_len, solution=solution)
        ENABLE_BLOCK_LOG = True if idx == 0 else False
        sender.init_application(sender_block_file_list[idx], ENABLE_BLOCK_LOG=ENABLE_BLOCK_LOG, **kwargs)
        senders.append(sender)

    emulator.senders = senders
    # reset net of emulator
    emulator.net = Engine(emulator.senders, emulator.links, **kwargs)

    return emulator


def create_mmgc_compete_emulator(solution, first_block_file, second_block_file, trace_file=None, **kwargs):
    emulator = create_multi_service_emulator(
        solution_list=[solution, None],
        sender_block_file_list=[first_block_file, second_block_file],
        trace_file=trace_file,
        **kwargs
    )

    return emulator


def create_emulator(solution, block_file, trace_file, second_block_file=None, **kwargs):
    if second_block_file:
        return create_mmgc_compete_emulator(solution, first_block_file=block_file, \
                    second_block_file=second_block_file, trace_file=trace_file, **kwargs)
    else:
        return SimpleEmulator(
                block_file=block_file,
                trace_file=trace_file,
                solution=solution,
                **kwargs
            )
