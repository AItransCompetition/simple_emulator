from player.congestion_control_algorithm import Solution as Cc_solution
from player.packet_selection import Solution as Packet_solution
from player.examples.reno import Reno

class Solution(Reno, Packet_solution):
    pass
