from utils import measure_time


class Solution(object):

    # @measure_time()
    def select_packet(self, cur_time, packet_queue):
        '''
        The alogrithm to select the packet which will be sended in next.
        The following example is selecting packet by the create time firstly, and radio of rest life time to deadline secondly.
        :param cur_time: float
        :param packet_queue: the list of Packet.You can get more detail about Block in objects/packet.py
        :return: int
        '''
        def is_better(packet):
            best_block_create_time = best_packet.block_info["Create_time"]
            packet_block_create_time = packet.block_info["Create_time"]
            # if packet is miss ddl
            if (cur_time - packet_block_create_time) >= packet.block_info["Deadline"]:
                return False
            if (cur_time - best_block_create_time) >= best_packet.block_info["Deadline"]:
                return True
            if best_block_create_time != packet_block_create_time:
                return best_block_create_time > packet_block_create_time
            return (cur_time - best_block_create_time) * best_packet.block_info["Deadline"] > \
                   (cur_time - packet_block_create_time) * packet.block_info["Deadline"]

        best_packet_idx = -1
        best_packet = None
        for idx, item in enumerate(packet_queue):
            if best_packet is None or is_better(item) :
                best_packet_idx = idx
                best_packet = item

        return best_packet_idx
