#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : utils
# @Function : 
# @Author : azson
# @Time : 2020/1/8 15:59
'''

import time, json
import matplotlib.pyplot as plt
import numpy as np
from config.constant import *
from config import constant


def get_ms_time(rate=1000):

    return time.time()*rate


def measure_time():
    def wraps(func):
        def measure(*args,**kwargs):
            start = time.time()
            res = func(*args,**kwargs)
            end = time.time()
            if constant.ENABLE_DEBUG:
                with open("output/funtion_time_test.log", "a") as f:
                    f.write("function %s use time %s\n"%(func.__name__, (end-start)))
            return res
        return measure
    return wraps


def analyze_emulator(log_file, trace_file=None, rows=None, time_range=None, scatter=False, file_range=None, sender=None):

    plt_data = []
    if file_range:
        plt_data = compose_packet_logs(file_range)
    else:
        with open(log_file, 'r') as f:
            for line in f.readlines():
                plt_data.append(json.loads(line.replace("'", '"')))
    if not sender:
        sender = [1]
    plt_data = list(filter(lambda x:x["Type"]=='A' and x["Position"] == 2 and x["Sender_id"] in sender, plt_data))
    if time_range:
        plt_data = time_filter(plt_data, time_range)
    # priority by packet id
    # plt_data = sorted(plt_data, key=lambda x:int(x["Packet_id"]))[:rows]
    if isinstance(rows, int):
        plt_data = plt_data[:rows]

    pic_nums = 1
    font_size = 50
    tick_size = 50

    data_latency = []
    data_finish_time = []
    data_drop = []
    data_sum_time = []
    # data_miss_ddl = []
    for idx, item in enumerate(plt_data):
        if item["Type"] == 'A':
            if item["Drop"] == 1:
                data_drop.append(idx)
            else:
                data_latency.append(item["Latency"])
                data_finish_time.append(item["Time"])
                data_sum_time.append(item["Send_delay"] + item["Pacing_delay"] + item["Latency"])

            # if item["Block_info"]["Deadline"] < data_sum_time[-1]:
            #     data_miss_ddl.append(idx)

    pic = plt.figure(figsize=(50, 30 * pic_nums))
    # plot latency distribution
    ax = plt.subplot(pic_nums, 1, 1)
    ax.set_title("Acked packet latency distribution", fontsize=font_size)
    ax.set_ylabel("Latency / s", fontsize=font_size)
    ax.set_xlabel("Time / s", fontsize=font_size)
    if scatter:
        ax.scatter(data_finish_time, data_latency, label="Latency", s=200)
    else:
        ax.plot(data_finish_time, data_latency, label="Latency", linewidth=5)

    ax.scatter([plt_data[idx]["Time"] for idx in data_drop],
               [min(data_latency) / 2]*len(data_drop), label="Drop", s=300, c='r', marker='x')

    # plot average latency
    ax.plot([0, data_finish_time[-1] ], [np.mean(data_latency)]*2, label="Average Latency", linewidth=5,
            c='g')
    plt.legend(fontsize=font_size)
    ax.set_xlim(data_finish_time[0] / 2, data_finish_time[-1] * 1.2)
    plt.tick_params(labelsize=tick_size)

    handles, labels = ax.get_legend_handles_labels()

    # plot bandwith
    if trace_file:
        tmp_ax = plot_trace(data_finish_time, ax, font_size, tick_size, trace_file)
        handles.extend(tmp_ax.get_legend_handles_labels()[0])
        labels.extend(tmp_ax.get_legend_handles_labels()[1])

    plt.legend(handles, labels, fontsize=font_size)

    plt.tight_layout()
    plt.legend(fontsize=font_size)
    plt.savefig("output/emulator-analysis.png")


def check_solution_format(input):

    if not isinstance(input, dict):
        raise TypeError("The return value should be a dict!")

    keys = ["cwnd", "send_rate"]
    if keys[0] in input or keys[1] in input:
        return input
    else:
        raise ValueError("One of the keys %s should in the return dict!" % (keys))


def get_emulator_info(sender_mi):

    event = {}
    event["Name"] = "Step"
    # event["Target Rate"] = sender_mi.target_rate
    event["Send Rate"] = sender_mi.get("send rate")
    event["Throughput"] = sender_mi.get("recv rate")
    event["Latency"] = sender_mi.get("avg latency")
    event["Loss Rate"] = sender_mi.get("loss ratio")
    event["Latency Inflation"] = sender_mi.get("sent latency inflation")
    event["Latency Ratio"] = sender_mi.get("latency ratio")
    event["Send Ratio"] = sender_mi.get("send ratio")
    # event["Cwnd"] = sender_mi.cwnd
    # event["Cwnd Used"] = sender_mi.cwnd_used

    return event


def analyze_application(acked_packets):
    pass


def get_packet_type(sender, packet):
    if packet.drop:
        return PACKET_TYPE_DROP
    if packet.packet_type == EVENT_TYPE_ACK and \
            packet.next_hop == len(sender.path):
        return PACKET_TYPE_FINISHED

    return PACKET_TYPE_TEMP


def debug_print(*args, **kwargs):
    if constant.ENABLE_DEBUG:
        print(*args, **kwargs)


def time_filter(data, time_range):
    if time_range[0] is None:
        time_range[0] = -1
    if time_range[1] is None:
        time_range[1] = data[-1]["Time"]
    data = list(filter(lambda x: time_range[0] <= x["Time"] <= time_range[1], data))
    return data


def compose_packet_logs(file_range, pattern=None):
    if pattern is None:
        pattern = "output/packet_log/packet-0.log"
    compose_data = []
    if file_range == "all":
        # Suppose maximum numbers of file is 1000
        file_range = [1000]
    try:
        for idx in range(*file_range):
            with open(pattern.replace("0", str(idx)), 'r') as f:
                for line in f.readlines():
                    compose_data.append(json.loads(line.replace("'", '"')))
    except Exception as e:
        debug_print("Log file ended at {}".format(idx))
    finally:
        return compose_data


def plot_cwnd(log_file, rows=None, trace_file=None, time_range=None, scatter=False, file_range=None, sender=None):
    if not constant.USE_CWND:
        print("Your congestion control don't use windows~")
        return
    plt_data = []
    if file_range:
        plt_data = compose_packet_logs(file_range)
    else:
        with open(log_file, 'r') as f:
            for line in f.readlines():
                plt_data.append(json.loads(line.replace("'", '"')))
    if not sender:
        sender = [1]
    # filter the packet at sender
    plt_data = list(filter(lambda x: x["Type"] == 'S' and x["Position"] == 0 and x["Sender_id"] in sender, plt_data))
    # plt_data = list(filter(lambda x: x["Drop"] == 0, plt_data))
    # filter by the time
    if time_range:
        plt_data = time_filter(plt_data, time_range)
    # plot "rows" counts data
    if isinstance(rows, int):
        plt_data = plt_data[:rows]

    pic_nums = 1
    font_size = 50
    tick_size = 50

    data_time = []
    data_cwnd = []
    data_Ucwnd = []
    last_cwnd = -1
    for item in plt_data:
        if item["Extra"]["Cwnd"] == last_cwnd:
            continue
        # last cwnd
        if last_cwnd != -1:
            data_time.append(item["Time"])
            data_cwnd.append(last_cwnd)

        last_cwnd = item["Extra"]["Cwnd"]
        data_time.append(item["Time"])
        data_cwnd.append(item["Extra"]["Cwnd"])
        data_Ucwnd.append(item["Waiting_for_ack_nums"])

    pic = plt.figure(figsize=(50, 30*pic_nums))
    # plot cwnd changing
    ax = plt.subplot(pic_nums, 1, 1)
    if scatter:
        ax.scatter(data_time, data_cwnd, label="cwnd", c='g', s=200)
    else:
        ax.plot(data_time, data_cwnd, label="cwnd", c='g', linewidth=5)
    ax.set_ylabel("Packet", fontsize=font_size)
    ax.set_xlabel("Time / s", fontsize=font_size)
    plt.tick_params(labelsize=tick_size)

    handles, labels = ax.get_legend_handles_labels()

    # plot bandwith
    if trace_file:
        tmp_ax = plot_trace(data_time, ax, font_size, tick_size, trace_file)
        handles.extend(tmp_ax.get_legend_handles_labels()[0])
        labels.extend(tmp_ax.get_legend_handles_labels()[1])

    plt.legend(handles, labels, fontsize=font_size)
    plt.savefig("output/cwnd_changing.png")


def plot_trace(data_time, ax, font_size, tick_size, trace_file):
    max_time = data_time[-1]
    trace_list = []
    with open(trace_file, "r") as f:
        for line in f.readlines():
            trace_list.append(list(
                map(lambda x: float(x), line.split(","))
            ))

    st = data_time[0]
    ax = ax.twinx()
    ed = -1
    for idx in range(1, len(trace_list)):
        if trace_list[idx][0] < st:
            continue
        if trace_list[idx][0] > max_time:
            ed = idx
            break
        ax.plot([st, trace_list[idx][0]], [trace_list[idx - 1][1] * 10 ** 6 / BYTES_PER_PACKET] * 2, '--',
                linewidth=5, c='b')
        st = trace_list[idx][0]

    if ed == -1 and trace_list[-1][0] < max_time:
        ax.plot([st, max_time], [trace_list[-1][1] * 10 ** 6 / BYTES_PER_PACKET] * 2, '--',
                label="Different Bandwith", linewidth=5, c='b')
    elif ed != -1:
        ax.plot([st, max_time], [trace_list[ed - 1][1] * 10 ** 6 / BYTES_PER_PACKET] * 2, '--',
                label="Different Bandwith", linewidth=5, c='b')

    ax.set_ylabel("Link bandwith (Packet/s)", fontsize=font_size)
    plt.tick_params(labelsize=tick_size)
    # plt.legend(fontsize=font_size)
    return ax


def plot_send_rate(log_file, rows=None, trace_file=None, time_range=None, scatter=False, file_range=None, sender=None):
    plt_data = []
    if file_range:
        plt_data = compose_packet_logs(file_range)
    else:
        with open(log_file, 'r') as f:
            for line in f.readlines():
                plt_data.append(json.loads(line.replace("'", '"')))
    if not sender:
        sender = [1]
    # filter the packet at receiver
    plt_data = list(
        filter(lambda x: x["Type"] == 'S' and x["Position"] == 0 and x["Drop"] == 0 and x["Sender_id"] in sender,
               plt_data))
    # plt_data = list(filter(lambda x: x["Drop"] == 0, plt_data))
    # filter by the time
    if time_range:
        plt_data = time_filter(plt_data, time_range)
    # plot "rows" counts data
    if isinstance(rows, int):
        plt_data = plt_data[:rows]

    pic_nums = 1
    font_size = 50
    tick_size = 50

    data_time = []
    data_rate = []
    data_inflight = []
    for idx, item in enumerate(plt_data):
        data_time.append(item["Time"])
        data_rate.append(item["Extra"]["Send_rate"])
        data_inflight.append(item["Waiting_for_ack_nums"])

    pic = plt.figure(figsize=(50, 30 * pic_nums))
    # plot cwnd changing
    ax = plt.subplot(pic_nums, 1, 1)
    if scatter:
        # ax.scatter(data_time, data_throughput, label="Throughput", c='g', s=200)
        ax.scatter(data_time, data_rate, label="Rate", c='black', s=200)
        # ax.scatter(data_time, data_inflight, label="Inflight", c='r', s=200)
    else:
        # ax.plot(data_time, data_throughput, label="Throughput", c='g')
        ax.plot(data_time, data_rate, label="Rate", c='black', linewidth=5)
        # ax.plot(data_time, data_inflight, label="Inflight", c='r', linewidth=5)
    ax.set_ylabel("Packet Numbers", fontsize=font_size)
    ax.set_xlabel("Time / s", fontsize=font_size)
    plt.tick_params(labelsize=tick_size)
    handles, labels = ax.get_legend_handles_labels()

    # plot bandwith
    if trace_file:
        tmp_ax = plot_trace(data_time, ax, font_size, tick_size, trace_file)
        handles.extend(tmp_ax.get_legend_handles_labels()[0])
        labels.extend(tmp_ax.get_legend_handles_labels()[1])

    plt.legend(handles, labels, fontsize=font_size)
    plt.savefig("output/send_rate_changing.png")


def plot_bbr(log_file, rows=None, trace_file=None, time_range=None, scatter=False, file_range=None, sender=None):
    plt_data = []
    if file_range:
        plt_data = compose_packet_logs(file_range)
    else:
        with open(log_file, 'r') as f:
            for line in f.readlines():
                plt_data.append(json.loads(line.replace("'", '"')))
    if not sender:
        sender = [1]
    # filter the packet at receiver
    plt_data = list(filter(lambda x: x["Type"] == 'A' and x["Position"] == 1 and x["Drop"] == 0 and x["Sender_id"] in sender, plt_data))
    # plt_data = list(filter(lambda x: x["Drop"] == 0, plt_data))
    # filter by the time
    if time_range:
        plt_data = time_filter(plt_data, time_range)
    # plot "rows" counts data
    if isinstance(rows, int):
        plt_data = plt_data[:rows]

    pic_nums = 1
    font_size = 50
    tick_size = 50

    data_time = []
    data_throughput = []
    data_bdp = []
    data_inflight = []
    for idx, item in enumerate(plt_data):
        if "delivered" not in item["Extra"]:
            continue
        if idx and item["Time"] < data_time[-1]:
            print("error order!")
        data_time.append(item["Time"])
        # used_time = (item["Time"] - item["Create_time"] - item["Send_delay"] - item["Pacing_delay"])
        used_time = item["Latency"]
        data_throughput.append((idx+1-item["Extra"]["delivered"]) / used_time)
        data_bdp.append(item["Extra"]["max_bw"] * item["Extra"]["min_rtt"] if item["Extra"]["max_bw"] != float("-inf") else 0)
        data_inflight.append(item["Waiting_for_ack_nums"])

    pic = plt.figure(figsize=(50, 30 * pic_nums))
    # plot cwnd changing
    ax = plt.subplot(pic_nums, 1, 1)
    if scatter:
        # ax.scatter(data_time, data_throughput, label="Throughput", c='g', s=200)
        ax.scatter(data_time, data_bdp, label="BDP", c='black', s=200)
        ax.scatter(data_time, data_inflight, label="Inflight", c='r', s=200)
    else:
        # ax.plot(data_time, data_throughput, label="Throughput", c='g')
        ax.plot(data_time, data_bdp, label="BDP", c='black', linewidth=5)
        ax.plot(data_time, data_inflight, label="Inflight", c='r', linewidth=5)
    ax.set_ylabel("Packet Numbers", fontsize=font_size)
    ax.set_xlabel("Time / s", fontsize=font_size)
    plt.tick_params(labelsize=tick_size)
    handles, labels = ax.get_legend_handles_labels()

    # plot bandwith
    if trace_file:
        tmp_ax = plot_trace(data_time, ax, font_size, tick_size, trace_file)
        handles.extend(tmp_ax.get_legend_handles_labels()[0])
        labels.extend(tmp_ax.get_legend_handles_labels()[1])

    plt.legend(handles, labels, fontsize=font_size)
    plt.savefig("output/bbr_changing.png")
    plt.show()


def plot_rate(log_file, rows=None, trace_file=None, time_range=None, scatter=False, file_range=None, sender=None, size=1):
    plt_data = []
    if file_range:
        plt_data = compose_packet_logs(file_range)
    else:
        with open(log_file, 'r') as f:
            for line in f.readlines():
                plt_data.append(json.loads(line.replace("'", '"')))
    if not sender:
        sender = [1]
    # filter the packet at receiver
    plt_data = list(
        filter(lambda x: x["Type"] == 'S' and x["Position"] == 0 and x["Drop"] == 0 and x["Sender_id"] in sender,
               plt_data))
    # filter by the time
    if time_range:
        plt_data = time_filter(plt_data, time_range)
    # plot "rows" counts data
    if isinstance(rows, int):
        plt_data = plt_data[:rows]

    pic_nums = 1
    font_size = 50
    tick_size = 50

    last_idx = 0
    data_time = []
    data_rate = []
    for idx, item in enumerate(plt_data):
        while plt_data[last_idx]["Time"] + size < item["Time"]:
            last_idx += 1
        if idx != last_idx and item["Time"] - plt_data[idx-1]["Time"] > 0.000001:
            # print(idx, last_idx, item["Time"], plt_data[last_idx]["Time"])
            data_time.append(item["Time"])
            data_rate.append((idx-last_idx+1)/(item["Time"] - plt_data[last_idx]["Time"]))

    pic = plt.figure(figsize=(50, 30 * pic_nums))
    # plot rate changing
    ax = plt.subplot(pic_nums, 1, 1)
    if scatter:
        ax.scatter(data_time, data_rate, label="Rate", c='black', s=200)
    else:
        ax.plot(data_time, data_rate, label="Rate", c='black', linewidth=5)
    ax.set_ylabel("Packet Numbers", fontsize=font_size)
    ax.set_xlabel("Time / s", fontsize=font_size)
    plt.tick_params(labelsize=tick_size)
    handles, labels = ax.get_legend_handles_labels()

    # plot bandwith
    if trace_file:
        tmp_ax = plot_trace(data_time, ax, font_size, tick_size, trace_file)
        handles.extend(tmp_ax.get_legend_handles_labels()[0])
        labels.extend(tmp_ax.get_legend_handles_labels()[1])

    plt.legend(handles, labels, fontsize=font_size)
    plt.savefig("output/rate_changing.png")


if __name__ == '__main__':

    log_packet_file = "output/packet_log/packet-0.log"
    trace_file = "config/trace.txt"
    new_trace_file = "scripts/first_group/traces_1.txt"
    # analyze_emulator(log_packet_file, time_range=None, scatter=False, trace_file=new_trace_file, file_range="all")
    # plot_cwnd(log_packet_file, None, trace_file=new_trace_file, time_range=None, scatter=False, file_range="all")
    plot_rate(log_packet_file, file_range="all", scatter=False)