class Packet(object):
    _packet_id = 1

    def __init__(self,
                 create_time,
                 next_hop,
                 offset,
                 payload,
                 packet_id=None,
                 packet_size=1500,
                 packet_type="S",
                 drop=False,
                 send_delay=.0,
                 pacing_delay=.0,
                 latency=.0,
                 block_info={},
                 retrans=False
                 ):
        self.packet_type = packet_type
        self.create_time = create_time
        self.finish_time = -1
        self.next_hop = next_hop
        self.offset = offset
        self.packet_id = packet_id
        self.payload = payload
        self.packet_size = packet_size
        self.drop = drop

        self.send_delay = send_delay
        self.pacing_delay = pacing_delay
        self.latency = latency
        self.extra = {}
        self.block_info = block_info
        self.decision_order = 0
        self.retrans = retrans

        if packet_id is None:
            self.packet_id = Packet._get_next_packet()

    @classmethod
    def _get_next_packet(cls):
        result = cls._packet_id
        cls._packet_id += 1
        return result

    @classmethod
    def create_normal_packet(cls, cur_time, **kwargs):
        return Packet(
                    create_time=cur_time,
                    next_hop=0,
                    offset=-1,
                    packet_size=kwargs["packet_size"],
                    payload=-1)

    def next_offset(self):
        if self.offset + 1 == self.block_info["Split_nums"] or self.retrans:
            return None
        payload = self.payload if self.offset + 2  < self.block_info["Split_nums"] else self.block_info["Size"] % self.payload

        return Packet(create_time=self.create_time,
                      next_hop=0,
                      offset=self.offset+1,
                      packet_size=self.packet_size,
                      payload=payload,
                      block_info=self.block_info,
                      send_delay=self.send_delay)

    def parse(self):

        return [self.packet_type,
                self.next_hop,
                self.latency,
                self.drop,
                self.packet_id]

    def get_rtt(self):
        return self.pacing_delay+self.latency

    def trans2dict(self):
        print_data = {
            "Type": self.packet_type,
            "Position": self.next_hop,
            "Send_delay": self.send_delay,
            "Pacing_delay" : self.pacing_delay,
            "Latency": self.latency,
            "Drop": 1 if self.drop else 0,
            "Packet_id": self.packet_id,
            "Create_time": self.create_time,
            "Offset" : self.offset,
            "Payload" : self.payload,
            "Packet_size" : self.packet_size,
            "Extra" : self.extra,
            "Block_info" : self.block_info
        }
        return print_data

    def create_retrans_packet(self, cur_time):
        """create a new packet for retransmission."""
        return Packet(create_time=cur_time,
                      next_hop=0,
                      offset=self.offset,
                      packet_size=self.packet_size,
                      payload=self.payload,
                      block_info=self.block_info,
                      retrans=True)

    def get_hash_val(self):
        """get the hash value of this packet according to it's member variables."""
        tmp = self.trans2dict()
        MOD = 1234567891
        ret = 0
        for key, val in tmp.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    ret = (ret * (hash(v)%MOD) ) % MOD
            else:
                ret = (ret * (hash(val)%MOD) ) % MOD
        return ret

    def is_miss_ddl(self, cur_time=None):
        # use current time to judge
        if cur_time and self.finish_time != -1:
            return cur_time > self.finish_time
        # for finished packet
        return cur_time-self.block_info["Create_time"] > self.block_info["Deadline"]

    def __lt__(self, other):
        return self.decision_order < other.decision_order

    def __str__(self):
        print_data = self.trans2dict()
        return str(print_data)