import collections
from collections import OrderedDict
from simpy.core import Environment
from typing import List


class Deque(object):
    'Fast searchable queue for default-tier'

    def __init__(self):
        self.od = OrderedDict()

    def appendleft(self, k):
        if k in self.od:
            del self.od[k]
        self.od[k] = None

    def pop(self):
        return self.od.popitem(0)[0]

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
    def __init__(self, name: str, max_size: int, granularity: int, latency: float, throughput: float,
                 target_occupation: float = 0.9):
        self.name = name
        self.max_size = max_size
        self.latency = latency
        self.throughput = throughput
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

        # LFU structure
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

    def read_packet(self, timestamp, tstart_tlast, name, size, priority):
        """
        :return: time in seconds until operation completion
        """
        for listener in self.listeners:
            listener.on_packet_access(timestamp, tstart_tlast, name, size, priority, False)

    def write_packet(self, timestamp, tstart_tlast, name, size, priority, drop="n"):
        """
        :return: time in seconds until operation completion
        """
        for listener in self.listeners:
            listener.on_packet_access(timestamp, tstart_tlast, name, size, priority, True, drop)


class Index:
    def __init__(self):
        self.index = dict()  # key: packet_name, value: tier/t1,t2,b1,b2

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
    def __init__(self, index: Index, tiers: List[Tier], env: Environment, default_tier_index: int = 0):
        self.index = index
        self._env = env
        self.tiers = tiers
        self.default_tier_index = default_tier_index

        for tier in tiers:
            tier.manager = self  # association linking

    def delay(self, timeout, cb):
        yield self._env.timeout(timeout)
        cb()

    def get_default_tier(self):
        return self.tiers[self.default_tier_index]
