#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : test_reno
# @Function : 
# @Author : azson
# @Time : 2020/3/10 17:19
'''
import json


def test_cwnd_internal(log_file, rows=None, time_range=None):
    raw_data = []
    with open(log_file, "r") as f:
        for line in f.readlines():
            raw_data.append(json.loads(line.replace("'", '"')))
    # filter the packet at sender
    s0_data = list(filter(lambda x: x["Type"] == 'S' and x["Position"] == 0, raw_data))
    # plt_data = list(filter(lambda x: x["Drop"] == 0, plt_data))
    # filter by the time
    if time_range:
        if time_range[0] is None:
            time_range[0] = -1
        if time_range[1] is None:
            time_range[1] = s0_data[-1]["Time"]
        s0_data = list(filter(lambda x: time_range[0] <= x["Time"] <= time_range[1], plt_data))
    # plot "rows" counts data
    if isinstance(rows, int):
        s0_data = s0_data[:rows]

    data_time = []
    data_cwnd = []
    data_Ucwnd = []
    last_cwnd = -1
    for item in s0_data:
        if item["Cwnd"] == last_cwnd:
            continue
        last_cwnd = item["Cwnd"]
        data_time.append(item["Time"])
        data_cwnd.append(item["Cwnd"])
        data_Ucwnd.append(item["Waiting_for_ack_nums"])


    raw_start_id = 0
    for i in range(1, len(data_time)):

        # send, ack, drop
        info = [0, 0, 0]
        send_packets = []
        ack_packets = []
        drop_packets = []
        for j in range(raw_start_id, len(raw_data)):
            if raw_data[j]["Time"] >= data_time[i]:
                raw_start_id = j
                break
            if raw_data[j]["Position"] == 1:
                continue
            if raw_data[j]["Drop"] == 1:
                drop_packets.append(raw_data[j]["Packet_id"])
                info[2] += 1
            elif raw_data[j]["Position"] == 0:
                send_packets.append(raw_data[j]["Packet_id"])
                info[0] += 1
            elif raw_data[j]["Position"] == 2:
                ack_packets.append(raw_data[j]["Packet_id"])
                info[1] += 1

        print('''
        Time [{0}, {1}),
        send {2} packets. {6}
        ack {3} packets. {7}
        drop {4} packets. {8}
        cwnd is {5} packets.
        '''.format(data_time[i-1], data_time[i], *info, data_cwnd[i-1],
                   send_packets, ack_packets, drop_packets))



if __name__ == '__main__':
    log_packet_file = "../output/packet_log/packet-0.log"

    test_cwnd_internal(log_packet_file)

