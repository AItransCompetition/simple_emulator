from player.congestion_control_algorithm import Solution as Cc_solution
from player.packet_selection import Solution as Packet_solution
# from player.examples.simple_bbr import BBR
from player.examples.match_trace_rate import MTR

class Solution(MTR, Packet_solution):
    pass
