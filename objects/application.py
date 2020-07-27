from objects.block import Block
from objects.packet import Packet
import numpy as np
import pandas as pd
from utils import debug_print
import json


class AppicationLayer(object):

    def __init__(self,
                 block_file,
                 create_det=0.1,
                 bytes_per_packet=1500,
                 **kwargs):
        self.extra = {}
        self.update_config(kwargs)
        self.block_file = block_file
        self.block_queue = []
        self.bytes_per_packet = bytes_per_packet

        self.block_nums = None
        self.init_time = .0
        self.pass_time = .0
        self.fir_log = True

        self.now_block = None
        self.now_block_offset = 0
        self.head_per_packet = 20

        self.create_det = create_det
        self.handle_block(block_file)
        self.ack_blocks = dict()
        self.blocks_status = dict()

    def update_config(self, extra):
        self.extra["ENABLE_BLOCK_LOG"] = extra["ENABLE_BLOG_LOG"] if "ENABLE_BLOCK_LOG" in extra else True
        self.run_dir = extra["RUN_DIR"]+'/' if "RUN_DIR" in extra else ''

    def handle_block(self, block_file):
        """
        creating block queue by "block_file".
        :param block_file: str
        :return:
        """
        if isinstance(block_file, str):
            block_file = [block_file]
        for single_file in block_file:
            if single_file[-4:] == ".csv":
                self.create_blok_by_csv(single_file)
            else:
                self.create_block_by_file(single_file, self.create_det)
        self.block_queue = sorted(self.block_queue, key=lambda x:x.timestamp)

    def create_blok_by_csv(self, csv_file):
        df_data = pd.read_csv(csv_file, header=None)
        shape = df_data.shape
        assert len(shape) >= 2
        if shape[1] == 2:
            df_data.columns = ["time", "size"]
        elif shape[1]== 3:
            df_data.columns = ["time", "size", "key_frame"]

        for idx in range(shape[0]):
            det = 1
            priority = 0
            deadline = 0.2
            # change priority
            if "video" in csv_file:
                priority = 2
            elif "audio" in csv_file:
                priority = 1
            if "priority-" in csv_file:
                priority = int(csv_file[int(csv_file.index("priority-") + len("priority-"))])
            # change deadline
            if "ddl-" in csv_file:
                st = csv_file.index("ddl-") + len("ddl-")
                for i in range(st, len(csv_file)):
                    if csv_file[i] == '-':
                        deadline = float(csv_file[st:i])
                        break
            # create block
            block = Block(bytes_size=float(df_data["size"][idx])*det,
                          deadline=deadline,
                          priority=priority,
                          timestamp=float(df_data["time"][idx]))
            self.block_queue.append(block)

    def create_block_by_file(self, block_file, det=0.1):
        with open(block_file, "r") as f:
            self.block_nums = int(f.readline())

            pattern_cols = ["type", "size", "ddl"]
            pattern=[]
            for line in f.readlines():
                pattern.append(
                    { pattern_cols[idx]:item.strip() for idx, item in enumerate(line.split(',')) }
                )

            peroid = len(pattern)
            for idx in range(self.block_nums):
                ch = idx % peroid
                block = Block(bytes_size=float(pattern[ch]["size"]),
                              deadline=float(pattern[ch]["ddl"]),
                              timestamp=self.init_time+self.pass_time+idx*det,
                              priority=pattern[ch]["type"])
                self.block_queue.append(block)

    def select_block(self):
        """select the block that not sent and return it  """
        cur_time = self.init_time + self.pass_time
        # Is it necessary ? filter block with missing ddl
        for idx in range(len(self.block_queue)-1, -1, -1):
            item = self.block_queue[idx]
            # if miss ddl in queue, clean and log
            if cur_time > item.timestamp + item.deadline:
                self.block_queue[idx].miss_ddl = 1
                self.log_block(self.block_queue[idx])
                self.block_queue.pop(idx)
        
        if len(self.block_queue) == 0:
            return None
        best_block = self.block_queue.pop(0)

        return best_block

    def get_next_packet(self, cur_time, mode=None):
        """
        get the packet that can be sent at "cur_time" and return it to sender.
        :param cur_time: float, current time.
        :param mode: if mode is "force", it will return the packet after cur_time in case of lacking of packet.
        :return: Packet.
        """
        self.pass_time = cur_time
        if self.now_block is None:
            self.now_block = self.select_block()
            if self.now_block is None:
                return None
            self.ack_blocks[self.now_block.block_id] = []
            self.now_block_offset = 0
            self.now_block.split_nums = int(np.ceil(self.now_block.size /
                                            (self.bytes_per_packet - self.head_per_packet)))
            self.blocks_status[self.now_block.block_id] = self.now_block

        # It will only send the packet that already created if mode is None;
        # else will update system time
        if mode != "force" and cur_time < self.now_block.timestamp:
            return None
        payload = self.bytes_per_packet - self.head_per_packet
        if self.now_block.size % (self.bytes_per_packet - self.head_per_packet) and \
                self.now_block_offset == self.now_block.split_nums - 1:
            payload = self.now_block.size % (self.bytes_per_packet - self.head_per_packet)

        packet = Packet(create_time=self.now_block.timestamp,
                          next_hop=0,
                          offset=0,
                          packet_size=self.bytes_per_packet,
                          payload=payload,
                          block_info=self.now_block.get_block_info()
                          )
        self.now_block = None
        return packet

    def update_block_status(self, packet, cur_time):
        """update the block finishing status according to the acknowledge packets pushed from sender."""
        block_id = packet.block_info["Block_id"]
        self.pass_time = cur_time
        # filter repeating acked packet
        if block_id in self.ack_blocks and   \
                packet.offset in self.ack_blocks[block_id]:
            return

        # update block information.
        # Which is better? Save packet individual value or sum value
        self.blocks_status[block_id].send_delay += packet.send_delay
        # whether or not take pacing delay into consideration?
        self.blocks_status[block_id].latency += packet.latency
        self.blocks_status[block_id].finished_bytes += packet.payload

        if block_id not in self.ack_blocks:
            self.ack_blocks[block_id] = [packet.offset]
        # retransmission packet may be sended many times
        else:
            self.ack_blocks[block_id].append(packet.offset)

        if self.is_sent_block(block_id):
            self.blocks_status[block_id].finish_timestamp = packet.finish_time
            self.log_block(self.blocks_status[block_id])

    def log_block(self, block):
        """logging the finished blocks or the blocks with missing deadline"""
        if not self.extra["ENABLE_BLOCK_LOG"]:
            return
        if self.fir_log:
            self.fir_log = False
            with open(self.run_dir+"output/block.log", "w") as f:
                pass

        if not self.is_sent_block(block.block_id):
            block.finish_timestamp = self.init_time + self.pass_time
        if block.is_miss_ddl():
            block.miss_ddl = 1

        with open(self.run_dir+"output/block.log", "a") as f:
            f.write(json.dumps(block.trans2dict())+'\n')

    def is_sent_block(self, block_id):
        """check whether or not the block with the id of "block_id" is finished."""
        if block_id in self.ack_blocks and \
                len(self.ack_blocks[block_id]) == self.blocks_status[block_id].split_nums:
            return True
        return False

    def close(self, cur_time):
        """do some operations when system is closing, like logging the blocks with the packets that have not been acked or sent."""
        self.pass_time = cur_time
        for block_id, packet_list in self.ack_blocks.items():
            if self.is_sent_block(block_id):
                continue
            debug_print("block {} not finished!".format(block_id))
            self.log_block(self.blocks_status[block_id])
        return None
