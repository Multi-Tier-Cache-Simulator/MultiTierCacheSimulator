import collections
from collections import OrderedDict
from simpy.core import Environment
from typing import List


class Packet:
    def __init__(self, packetType, name, size, priority):
        self.packetType = packetType
        self.name = name
        self.size = size
        self.priority = priority


class Deque(object):
    'Fast searchable queue for default-tier'

    def __init__(self):
        self.od = OrderedDict()

    def appendleft(self, key, value):
        if key in self.od:
            del self.od[key]
        self.od[key] = value

    def pop(self):
        return self.od.popitem(0)[1]

    def remove(self, k):
        del self.od[k]

    def __len__(self):
        return len(self.od)

    def __iter__(self):
        return reversed(self.od)

    def __contains__(self, k):
        return k in self.od

    def __repr__(self):
        return 'Deque(%r)' % (list(self),)


class Tier:
    def __init__(self, name: str, max_size: int, granularity: int, latency: float, read_throughput: float,
                 write_throughput: float,
                 target_occupation: float = 0.9):
        """
        :param max_size: octets
        :param latency: nanoseconds
        :param throughput: O/nanoseconds
        :param granularity: block size
        :param target_occupation: [0.0, 1.0[, the maximum allowed used capacity ratio
        """
        self.name = name
        self.max_size = max_size
        self.latency = latency
        self.read_throughput = read_throughput
        self.write_throughput = write_throughput
        self.target_occupation = target_occupation
        self.granularity = granularity

        self.manager = None
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

        self.chr = 0  # cache hit ratio
        self.cmr = 0  # cache miss ratio

        self.p = 0  # Target size for the list T1

        # Random structure
        self.random_struct = dict()

        # LFU params
        self.min_freq = float("inf")
        self.freq_to_nodes = collections.defaultdict(collections.OrderedDict)
        self.key_to_freq = {}

        # LRU structure
        self.lru_dict = OrderedDict()
        self.last_completion_time = 0

        # ARC structure
        # L1: only once recently
        self.t1 = Deque()  # T1: recent cache entries
        self.b1 = Deque()  # B1: ghost entries recently evicted from the T1 cache

        # L2: at least twice recently
        self.t2 = Deque()  # T2: frequent entries
        self.b2 = Deque()  # B2: ghost entries recently evicted from the T2 cache

    def register_listener(self, listener: "Policy"):
        self.listeners += [listener]

    def read_packet(self, tstart_tlast, packet):
        for listener in self.listeners:
            listener.on_packet_access(tstart_tlast, packet, False)

    def write_packet(self, tstart_tlast, packet, drop="n", cause=None):
        for listener in self.listeners:
            listener.on_packet_access(tstart_tlast, packet, True, drop)

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
    def __init__(self):
        self.index = dict()  # key: packet_name, value: tier

    def __str__(self):
        print("index")
        for key, value in self.index.items():
            print(key + value.name, end="")
        print(" ")

    # return the tier where the packet is
    def get_packet_tier(self, name: str):
        if name in self.index.keys():
            return self.index[name]
        else:
            return -1

    def tier_has_packet(self, tier: Tier, name: str):
        if self.index[name] == tier:
            return True
        else:
            return False

    # update index
    def update_packet_tier(self, name: str, tier: Tier):
        self.index[name] = tier

    def del_packet(self, name: str):
        self.index.pop(name)


class StorageManager:
    def __init__(self, index: Index, tiers: List[Tier], env: Environment, slot_size: int, default_tier_index: int = 0):
        self.index = index
        self._env = env
        self.tiers = tiers
        self.default_tier_index = default_tier_index
        self.slot_size = slot_size

        for tier in tiers:
            tier.manager = self  # association linking

    def get_default_tier(self):
        return self.tiers[self.default_tier_index]
