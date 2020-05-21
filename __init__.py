import os, sys, inspect, platform

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, parentdir+"/simple_emulator")
# print(sys.path)

from objects.pcc_emulator import PccEmulator
from objects.cc_base import CongestionControl
from player.packet_selection import Solution as Packet_selection
from utils import *
from config.constant import *
from config import constant

from player.examples.reno import Reno
# from player.examples.simple_bbr import BBR
# from player.examples.RL import RL
from double_flow import create_2flow_emulator
from qoe_model import cal_qoe

# from scripts.block_trace_generator import generate_block_trace
# from scripts.network import create_network, create_trace


__all__ = ["PccEmulator", "CongestionControl", "Packet_selection", \
           "analyze_pcc_emulator", "plot_cwnd", "plot_rate", \
           "Reno", "create_2flow_emulator", "constant", \
           "cal_qoe"]

block_file = parentdir+"/simple_emulator"+"/config/block.txt"
trace_file = parentdir+"/simple_emulator"+"/config/trace.txt"
log_file = "output/pcc_emulator.log"
log_packet_file = "output/packet_log/packet-0.log"

new_trace_file = parentdir+"/simple_emulator"+"scripts/first_group/traces_1.txt"
new_block_files = [parentdir+"/simple_emulator"+"config/data_video.csv", parentdir+"/simple_emulator"+"config/data_audio.csv"]

try:
    if os.path.exists("output"):
        if platform.system() == "Windows":
            # for windows
            os.system("rmdir /Q /S output")
        else:
            # for linux
            os.system("rm -rf output")

    # os.rmdir("output")
    os.mkdir("output")
    os.mkdir("output/packet_log")

except Exception as e:
    pass

# emulator = PccEmulator(
#     block_file=block_file,
#     trace_file=trace_file,
#     queue_range=(MIN_QUEUE, MAX_QUEUE)
# )
