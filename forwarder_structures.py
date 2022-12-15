import collections
from collections import OrderedDict
from simpy.core import Environment
from typing import List


class Deque(object):
    """Fast searchable queue for default-tier"""

    def __init__(self):
        self.od = OrderedDict()

    def __str__(self):
        for key, value in self.od.items():
            print(value.size.__str__() + ", ", end="")
        print(" ")

    def __len__(self):
        return len(self.od)

    def __contains__(self, k):
        return k in self.od

    def append_left(self, key, value):
        if key in self.od:
            del self.od[key]
        self.od[key] = value

    def pop(self):
        return self.od.popitem(0)[1]

    def remove(self, k):
        del self.od[k]


class Packet:
    def __init__(self, data_back, timestamp, name, size, priority):
        self.data_back = data_back
        self.name = name
        self.size = size
        self.priority = priority
        self.timestamp = timestamp

    def __str__(self):
        print(self.data_back.__str__() + ", " + self.name.__str__() + ", " + self.size.__str__() + ", ")


class PIT:
    def __init__(self):
        self.pit = dict()  # key: packet_name, value: expiration_time

    def __str__(self):
        for packet_name, expiration_time in self.pit.items():
            print(packet_name + ":" + expiration_time.__str__(), end=", ")
        print(" ")

    def pit_has_name(self, packet_name: str):
        if packet_name in self.pit:
            return True
        else:
            return False

    def get_pit_entry(self, packet_name: str):
        return self.pit[packet_name]

    def add_to_pit(self, packet_name: str, expiration_time: int):
        self.pit[packet_name] = expiration_time

    def del_from_pit(self, packet_name: str):
        self.pit.pop(packet_name)

    def update_pit_times(self, env: Environment):
        self.pit = {packet_name: expiration_time for packet_name, expiration_time in self.pit.items() if
                    self.get_pit_entry(packet_name) > env.now}


class Tier:
    def __init__(self, name: str, max_size: int, granularity: int, latency: float, read_throughput: float,
                 write_throughput: float,
                 target_occupation: float = 0.9):
        """""
        :param max_size: octets
        :param latency: nanoseconds
        :param write_throughput: o/nanoseconds
        :param read_throughput: o/nanoseconds
        :param granularity: block size
        :param target_occupation: [0.0, 1.0[, the maximum allowed used capacity ratio
        """""
        self.name = name
        self.max_size = max_size
        self.latency = latency
        self.read_throughput = read_throughput
        self.write_throughput = write_throughput
        self.target_occupation = target_occupation
        self.granularity = granularity

        self.forwarder = None
        self.listeners = []
        self.used_size = 0
        self.number_of_packets = 0
        self.number_of_reads = 0
        self.number_of_write = 0

        self.number_of_eviction_from_this_tier = 0
        self.number_of_eviction_to_this_tier = 0
        self.number_of_prefetching_from_this_tier = 0
        self.number_of_prefetching_to_this_tier = 0

        self.time_spent_reading = 0
        self.time_spent_writing = 0
        self.high_p_data_retrieval_time = 0
        self.low_p_data_retrieval_time = 0

        self.chr = 0  # cache hit ratio
        self.chr_hpc = 0  # cache hit ratio for high priority content
        self.chr_lpc = 0  # cache hit ratio for low priority content
        self.cmr = 0  # cache miss ratio

        # Random structure
        self.random_struct = dict()

        # LFU structure
        self.freqToKey = collections.defaultdict(dict)  # frequency to dict of <key, val>
        self.keyToFreq = collections.defaultdict(int)
        self.keyToVal = collections.defaultdict(int)

        # LRU structure
        self.lru_dict = OrderedDict()

        # ARC structure
        self.p = 0  # Target size for the list T1
        # L1: only once recently
        self.t1 = Deque()  # T1: recent cache entries
        # self.b1 = Deque()  # B1: ghost entries recently evicted from the T1 cache
        # L2: at least twice recently
        self.t2 = Deque()  # T2: frequent entries
        # self.b2 = Deque()  # B2: ghost entries recently evicted from the T2 cache

        # disk structure
        self.submission_queue = []
        self.submission_queue_max_size = 64

    def register_listener(self, listener: "Policy"):
        self.listeners += [listener]

    def read_packet(self, env: Environment, res, packet):
        for listener in self.listeners:
            env.process(listener.on_packet_access(env, res, packet, False))

    def write_packet(self, env: Environment, res, packet, cause=None):
        for listener in self.listeners:
            env.process(listener.on_packet_access(env, res, packet, True))

        if cause is not None:
            if cause == "eviction":
                self.number_of_eviction_to_this_tier += 1
            elif cause == "prefetching":
                self.number_of_prefetching_to_this_tier += 1
            else:
                raise RuntimeError(f'Unknown cause {cause}. Expected "eviction", "prefetching" or None')

    def prefetch_packet(self, packet):
        for listener in self.listeners:
            listener.prefetch_packet(packet)


class Index:
    # add the time of writing to the index as well ?
    def __init__(self):
        self.active_index = dict()  # key: packet_name, value: tier
        self.ghost_index = dict()  # key: packet_name, value: b1 or b2

    def __str__(self, what='index'):
        if what == 'index':
            print("index")
            for packet_name, tier in self.active_index.items():
                print(packet_name + ':' + tier.name, end=", ")
            print(" ")
        else:
            print("ghost index")
            for packet_name, queue_name in self.ghost_index.items():
                print(packet_name + ':' + queue_name, end=", ")
            print(" ")

    # index
    def get_packet_tier(self, packet_name: str):
        if packet_name in self.active_index.keys():
            return self.active_index[packet_name]
        else:
            print('packet not in cs')
            return -1

    def cs_has_packet(self, packet_name: str):
        if packet_name in self.active_index:
            return True
        else:
            return False

    def packet_in_tier(self, packet_name: str, tier: Tier):
        if self.active_index[packet_name] == tier:
            return True
        else:
            return False

    def update_packet_tier(self, packet_name: str, tier: Tier):
        self.active_index[packet_name] = tier

    def del_packet_from_cs(self, packet_name: str):
        self.active_index.pop(packet_name)

    # ghost index
    def packet_in_queue(self, packet_name: str, queue_name: str):
        if packet_name in self.ghost_index.keys():
            if self.ghost_index[packet_name] == queue_name:
                return True
            else:
                return False
        else:
            return False

    def update_packet_queue(self, packet_name: str, queue_name: str):
        self.ghost_index[packet_name] = queue_name

    def del_packet_from_queues(self, packet_name: str):
        self.ghost_index.pop(packet_name)

    def pop_packet_from_queue(self, queue_name: str):
        q_name = [packet_name for packet_name in self.ghost_index.keys() if
                  self.ghost_index[packet_name] == queue_name]
        packet_name = q_name[0]
        self.ghost_index.pop(packet_name)

    def queue_len(self, queue_name: str):
        return len([packet_name for packet_name in self.ghost_index.keys() if
                    self.ghost_index[packet_name] == queue_name])


class Forwarder:
    def __init__(self, env: Environment, index: Index, tiers: List[Tier], pit: PIT, slot_size: int,
                 default_tier_index: int = 0):
        self._env = env

        # content store
        # index
        self.index = index
        # tiers
        self.tiers = tiers

        # pit table
        self.pit = pit

        # number of aggregation
        self.nAggregation = 0

        # default tier
        self.default_tier_index = default_tier_index

        # slot size
        self.slot_size = slot_size

        # association linking
        for tier in tiers:
            tier.forwarder = self

    def get_default_tier(self):
        return self.tiers[self.default_tier_index]
