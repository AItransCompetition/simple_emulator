import json, random, os, inspect, shutil
import numpy as np

from utils import (
    get_emulator_info, measure_time
)
from objects.sender import Sender
from objects.link import Link
from objects.engine import Engine

from player.aitrans_solution import Solution as Aitrans_solution
from config import constant

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
if "simple_emulator" not in parentdir:
    parentdir += "simple_emulator"


class SimpleEmulator(object):

    def __init__(self,
                 block_file=None,
                 trace_file=None,
                 queue_range=None,
                 solution=None,
                 **kwargs):
        self.extra = kwargs
        # do configure on constant
        self.update_config(kwargs)

        self.trace_cols = ("time", "bandwith", "loss_rate", "delay")
        self.queue_range = queue_range if queue_range else (constant.MIN_QUEUE, constant.MAX_QUEUE)
        self.trace_file = trace_file if trace_file else parentdir + "/config/trace.txt"
        if isinstance(self.trace_file, int):
            self.trace_file = parentdir + "/scripts/first_group/traces_%d.txt" % self.trace_file
        self.block_file = block_file if block_file else parentdir + "/config/block.txt"
        self.event_record = { "Events" : [] }

        # unkown params
        self.features = [] # ["send rate", "recv rate"]
        self.history_len = 1
        self.steps_taken = 0

        self.links = None
        self.senders = None
        self.solution = solution
        self.trace_list = None

        if "senders" not in kwargs and "links" not in kwargs:
            self.create_new_links_and_senders()
        if "senders" in kwargs:
            self.senders = kwargs["senders"]
            kwargs.pop("senders")
        if "links" in kwargs:
            self.links = kwargs["links"]
            kwargs.pop("links")
        self.net = Engine(self.senders, self.links, **kwargs)

    def update_config(self, extra):
        """make it available that change some variable in constant.py by the way of transmitting function parameters."""
        if "USE_CWND" in extra:
            constant.USE_CWND = extra["USE_CWND"]
        if "ENABLE_DEBUG" in extra:
            constant.ENABLE_DEBUG = extra["ENABLE_DEBUG"]
        if "ENABLE_LOG" in extra:
            constant.ENABLE_LOG = extra["ENABLE_LOG"]
        if "ENABLE_HASH_CHECK" in extra:
            constant.ENABLE_HASH_CHECK = extra["ENABLE_HASH_CHECK"]
        if "MAX_PACKET_LOG_ROWS" in extra:
            constant.ENABLE_LOG = extra["MAX_PACKET_LOG_ROWS"]
        if "MIN_QUEUE" in extra:
            constant.MIN_QUEUE = extra["MIN_QUEUE"]
        if "MAX_QUEUE" in extra:
            constant.MAX_QUEUE = extra["MAX_QUEUE"]
        if "SEED" in extra:
            random.seed(extra["SEED"])
        if "USE_LATENCY_NOISE" in extra:
            constant.USE_LATENCY_NOISE = extra["USE_LATENCY_NOISE"]
        if "MAX_LATENCY_NOISE" in extra:
            constant.MAX_LATENCY_NOISE = extra["MAX_LATENCY_NOISE"]
        # init output directory
        self.extra["RUN_DIR"] = extra["RUN_DIR"] if "RUN_DIR" in extra else "."
        try:
            if os.path.exists(self.extra["RUN_DIR"] + "/output"):
                shutil.rmtree(self.extra["RUN_DIR"] + "/output")
            os.mkdir(self.extra["RUN_DIR"] + "/output")
            os.mkdir(self.extra["RUN_DIR"] + "/output/packet_log")
        except Exception as e:
            # print(extra["RUN_DIR"] + "/output")
            pass

    def get_trace(self):
        """init the "trace_list" according to the trace file."""
        trace_list = []
        with open(self.trace_file, "r") as f:
            for line in f.readlines():
                trace_list.append(list(
                    map(lambda x: float(x), line.split(","))
                ))
                if len(trace_list[-1]) != len(self.trace_cols):
                    raise ValueError("Trace file error!\nPlease check its format like : {0}".format(self.trace_cols))

        if len(trace_list) == 0:
            raise ValueError("Trace file error!\nThere is no data in the file!")

        return trace_list

    def create_new_links_and_senders(self):
        """create links and senders in this network."""
        self.trace_list = self.get_trace()
        # queue = 1 + int(np.exp(random.uniform(*self.queue_range)))
        # print("queue size : %d" % queue)
        # bw = self.trace_list[0][1]

        queue = int(random.uniform(*self.queue_range))
        self.links = [Link(self.trace_list, queue) , Link([], queue, delay=self.trace_list[0][3])]
        #self.senders = [Sender(0.3 * bw, [self.links[0], self.links[1]], 0, self.history_len)]
        #self.senders = [Sender(random.uniform(0.2, 0.7) * bw, [self.links[0], self.links[1]], 0, self.history_len)]
        solution = Aitrans_solution() if not self.solution else self.solution
        # support change type of cc by aitrans solution
        if hasattr(solution, "USE_CWND"):
            constant.USE_CWND = solution.USE_CWND

        self.senders = [Sender(self.links, 0, self.features,
                               history_len=self.history_len, solution=solution)]
        for item in self.senders:
            item.init_application(self.block_file, **self.extra)

    # @measure_time()
    def run_for_dur(self, during_time=float("inf")):
        """run this emulator for time of "dur_time"."""
        # action = [0.9, 0.9]
        # for i in range(len(self.senders)):
        #     self.senders[i].apply_rate_delta(action[0])
        #     if USE_CWND:
        #         self.senders[i].apply_cwnd_delta(action[1])

        reward = self.net.run_for_dur(during_time)
        for sender in self.senders:
            sender.record_run()

        sender_obs = self._get_all_sender_obs()
        sender_mi = self.senders[0].get_run_data()
        event = get_emulator_info(sender_mi)
        event["reward"] = reward
        self.event_record["Events"].append(event)
        if event["Latency"] > 0.0:
            self.run_dur = 0.5 * sender_mi.get("avg latency")

        return event, sender_obs

    def print_debug(self):
        print("---Link Debug---")
        for link in self.links:
            link.print_debug()
        print("---Sender Debug---")
        for sender in self.senders:
            sender.print_debug()

    def reset(self):
        self.steps_taken = 0
        self.net.reset()
        self.create_new_links_and_senders()
        self.net = Engine(self.senders, self.links)
        self.episodes_run += 1
        if self.episodes_run > 0 and self.episodes_run % 100 == 0:
            self.dump_events_to_file("pcc_env_log_run_%d.json" % self.episodes_run)
        self.event_record = {"Events": []}
        self.net.run_for_dur(self.run_dur)
        self.net.run_for_dur(self.run_dur)
        self.reward_ewma *= 0.99
        self.reward_ewma += 0.01 * self.reward_sum
        print("Reward: %0.2f, Ewma Reward: %0.2f" % (self.reward_sum, self.reward_ewma))
        self.reward_sum = 0.0
        return self._get_all_sender_obs()

    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None

    def dump_events_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.event_record, f, indent=4)

    def _get_all_sender_obs(self):
        sender_obs = self.senders[0].get_obs()
        sender_obs = np.array(sender_obs).reshape(-1, )
        # print(sender_obs)
        return sender_obs


