#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : block_trace_generator
# @Function : 
# @Author : azson
# @Time : 2020/4/23 9:18
'''
import random


def generate_block_trace(network_trace, avg_block_size=200000, dur_sec=15, use_noisy=False, output_file="data_block.csv"):
    trace_list = []
    block_list = []
    with open(network_trace, "r") as f:
        for line in f.readlines():
            trace_list.append(list(
                map(lambda x: float(x), line.split(","))
            ))
    cur_time = 0
    for idx, item in enumerate(trace_list):
        time, bw, loss_rate, p_time = item
        bw *= 10**6
        if idx == 0:
            continue
        end_time = trace_list[-1][0]+5 if idx == len(trace_list)-1 else trace_list[idx+1][0]
        end_time = min(end_time, dur_sec)
        while cur_time < end_time:
            new_block_create_time = cur_time
            new_block_size = avg_block_size
            if use_noisy:
                new_block_size = new_block_size * (0.9+0.2*random.random())

            block_list.append([new_block_create_time, new_block_size])
            cur_time += new_block_size / bw
        if cur_time >= dur_sec:
            break
    if output_file:
        with open(output_file, 'w') as f:
            for line in block_list:
                f.write(','.join(list(map(lambda x:str(x), line))))
                f.write('\n')

    return block_list



if __name__ == '__main__':
    # network_trace = "first_group/traces_1.txt"
    network_trace = "../config/trace.txt"
    block_trace = generate_block_trace(network_trace, use_noisy=True)
    print(block_trace)
    print(len(block_trace))