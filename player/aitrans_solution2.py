from player.congestion_control_algorithm import Solution as Cc_solution
from player.packet_selection import Solution as Packet_solution
# from player.examples.simple_bbr import BBR

class Solution(Cc_solution, Packet_solution):
    pass
