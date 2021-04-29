import os, sys, inspect, platform

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, parentdir+"/simple_emulator")
# print(sys.path)

from objects.emulator import SimpleEmulator
from objects.cc_base import CongestionControl
from player.block_selection import Solution as BlockSelection
from utils import *
from config.constant import *
from config import constant

from player.examples.reno import Reno
from double_flow import create_2flow_emulator, create_multi_service_emulator, create_mmgc_compete_emulator, create_emulator
from qoe_model import cal_qoe


__all__ = ["SimpleEmulator", "CongestionControl", "BlockSelection", \
           "analyze_emulator", "plot_cwnd", "plot_rate", \
           "Reno", "create_2flow_emulator", "constant", \
           "create_multi_service_emulator", "create_mmgc_compete_emulator", "create_emulator", \
           "cal_qoe"]
