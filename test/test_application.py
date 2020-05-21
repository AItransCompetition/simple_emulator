#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : test_block
# @Function : 
# @Author : azson
# @Time : 2020/3/12 16:50
'''

from config.constant import *
import pandas as pd


def pred_packet_nums():

    total_packet_nums = 0
    total_block_nums = 0
    time_range = [float("inf"), -1]
    for single_file in new_block_files:
        df_data = pd.read_csv(single_file, header=None)
        total_block_nums += df_data.shape[0]

        unit_size = BYTES_PER_PACKET - HEAD_PER_PACKAET
        c = 0
        while True:
            det = sum(df_data[1] >= unit_size*c)
            if det == 0:
                break
            c += 1
            total_packet_nums += det

        # update time
        time_range[0] = min(time_range[0], min(df_data[0]))
        time_range[1] = max(time_range[1], max(df_data[0]))

    print("Time [{}, {}] : \nAt least send {} packets\nThere are {} blocks".format(
        *time_range, total_packet_nums, total_block_nums
    ))


def filter_log():
    log_packet_file = "../output/packet_log/packet-0.log"
    filter_condition = {
        "Block_id" : 1,
        "Offset" : 3
    }
    output_keys = ["Time", "Cwnd", "Waiting_for_ack_nums", \
                   "Type", "Position", "Block_id", "Offset", "Packet_id"]

    data = []
    with open(log_packet_file, "r") as f:
        for line in f.readlines():
            # print(line)
            dt = eval(line)
            f = True
            for key, val in filter_condition.items():
                if dt[key] != val:
                    f = False
                    break
            if f:
                new_dt = dict()
                for key in output_keys:
                    if key in dt:
                        new_dt[key] = dt[key]
                data.append(new_dt)

    with open("test_application.output", "w") as f:
        for line in data:
            f.write(str(line)+"\n")


if __name__ == '__main__':
    new_block_files = ["../config/data_video.csv", "../config/data_audio.csv"]

    pred_packet_nums()
    # filter_log()