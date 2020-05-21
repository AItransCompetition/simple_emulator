"""
This demo aims to help player running system quickly by using the pypi library DTP-Emualtor https://pypi.org/project/DTP-Emulator/.
"""
from simple_emulator import PccEmulator, CongestionControl

# We provided a simple algorithms about packet selection to help you being familiar with this competition.
# In this example, it will select the packet according to packet's created time first and radio of rest life time to deadline secondly.
from simple_emulator import Packet_selection

# We provided some simple algorithms about congestion control to help you being familiar with this competition.
# Like Reno and an example about reinforcement learning implemented by tensorflow
from simple_emulator import Reno
# Ensuring that you have installed tensorflow before you use it
# from simple_emulator import RL

# We provided some function of plotting to make you analyze result easily in utils.py
from simple_emulator import analyze_pcc_emulator, plot_cwnd, plot_rate


# Your solution should include packet selection and congestion control.
# So, we recommend you to achieve it by inherit the objects we provided and overwritten necessary method.
class MySolution(Packet_selection, Reno):

    def select_packet(self, cur_time, packet_queue):
        """
        The algorithm to select which packet in 'packet_queue' should be sent at time 'cur_time'.
        See more at https://github.com/Azson/DTP-emulator/tree/pcc-emulator#packet_selectionpy.
        """
        return super().select_packet(cur_time, packet_queue)

    def make_decision(self, cur_time):
        """
        The part of algorithm to make congestion control, which will be call when sender need to send pacekt.
        See more at https://github.com/Azson/DTP-emulator/tree/pcc-emulator#congestion_control_algorithmpy.
        """
        return super().make_decision(cur_time)

    def append_input(self, data):
        """
        The part of algorithm to make congestion control, which will be call when sender get an event about acknowledge or lost from reciever.
        See more at https://github.com/Azson/DTP-emulator/tree/pcc-emulator#congestion_control_algorithmpy.
        """
        return super().append_input(data)


# The file path of packets' log
log_packet_file = "output/packet_log/packet-0.log"

# Use the object you created above
my_solution = MySolution()

# Create the emulator using your solution
# Specify USE_CWND to decide whether or not use crowded windows. USE_CWND=True by default.
# Specify ENABLE_LOG to decide whether or not output the log of packets. ENABLE_LOG=True by default.
# You can get more information about parameters at https://github.com/Azson/DTP-emulator/tree/pcc-emulator#constant
emulator = PccEmulator(
    solution=my_solution,
    USE_CWND=True,
    ENABLE_LOG=True
)

# Run the emulator and you can specify the time for the emualtor's running.
# It will run until there is no packet can sent by default.
emulator.run_for_dur()

# print the debug information of links and senders
emulator.print_debug()

# Output the picture of pcc_emulator-analysis.png
# You can get more information from https://github.com/Azson/DTP-emulator/tree/pcc-emulator#pcc_emulator-analysispng.
analyze_pcc_emulator(log_packet_file, file_range="all")

# Output the picture of cwnd_changing.png
# You can get more information from https://github.com/Azson/DTP-emulator/tree/pcc-emulator#cwnd_changingpng
plot_cwnd(log_packet_file, file_range="all")