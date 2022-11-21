import collections
from collections import OrderedDict
from simpy.core import Environment
from typing import List
from collections import defaultdict


class Node(object):
    def __init__(self, key, value):
        self.key, self.value = key, value
        self.prev, self.nxt = None, None
        return


class DoubleLinkedList(object):
    def __init__(self):
        self.head_sentinel, self.tail_sentinel, self.count = Node(None, None), Node(None, None), 0
        self.head_sentinel.nxt, self.tail_sentinel.prev = self.tail_sentinel, self.head_sentinel
        self.count = 0

    def insert(self, x, node):
        if node is None:
            raise
        temp = x.nxt
        x.nxt, node.prev = node, x
        node.nxt, temp.prev = temp, node
        self.count += 1

    def appendleft(self, node):
        if node is None:
            raise
        self.insert(self.head_sentinel, node)

    def append(self, node):
        if node is None:
            raise
        self.insert(self.get_tail(), node)

    def remove(self, node):
        if node is None:
            raise
        prev_node = node.prev
        prev_node.nxt, node.nxt.prev = node.nxt, prev_node
        self.count -= 1

    def pop(self):
        if self.size() < 1:
            raise
        self.remove(self.get_tail())

    def popleft(self):
        if self.size() < 1:
            raise
        self.remove(self.get_head())

    def size(self):
        return self.count

    def get_head(self):
        return self.head_sentinel.nxt if self.count > 0 else None

    def get_tail(self):
        return self.tail_sentinel.prev if self.count > 0 else None


class LinkedHashSet:
    def __init__(self):
        self.node_map, self.dll = {}, DoubleLinkedList()

    def size(self):
        return len(self.node_map)

    def contains(self, key):
        return key in self.node_map

    def search(self, key):
        if not self.contains(key):
            raise
        return self.node_map[key].value

    def appendleft(self, key, value):
        if not self.contains(key):
            node = Node(key, value)
            self.dll.appendleft(node)
            self.node_map[key] = node
        else:
            self.node_map[key].value = value
            self.moveleft(key)

    def append(self, key, value):
        if not self.contains(key):
            node = Node(key, value)
            self.dll.append(node)
            self.node_map[key] = node
        else:
            self.node_map[key].value = value
            self.moveright(key)

    def moveleft(self, key):
        if not self.contains(key):
            raise
        node = self.node_map[key]
        self.dll.remove(node)
        self.dll.appendleft(node)

    def moveright(self, key):
        if not self.contains(key):
            raise
        node = self.node_map[key]
        self.dll.remove(node)
        self.dll.append(node)

    def remove(self, key):
        if not self.contains(key):
            raise
        node = self.node_map[key]
        self.dll.remove(node)
        self.node_map.pop(key)

    def popleft(self):
        key = self.dll.get_head().key
        self.remove(key)
        return key

    def pop(self):
        key = self.dll.get_tail().key
        self.remove(key)
        return key


class Deque(object):
    """Fast searchable queue for default-tier"""

    def __init__(self):
        self.od = OrderedDict()

    def appendleft(self, key, value):
        if key in self.od:
            del self.od[key]
        self.od[key] = value

    def __str__(self):
        for key, value in self.od.items():
            print(value.size.__str__() + ", ", end="")
        print(" ")

    def pop(self):
        return self.od.popitem(0)[1]

    def __get__(self, k):
        return self.od[k]

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


class Packet:
    def __init__(self, packetType, timestamp, name, size, priority):
        self.packetType = packetType
        self.name = name
        self.size = size
        self.priority = priority
        self.timestamp = timestamp

    def __str__(self):
        print(self.packetType.__str__() + ", " + self.name.__str__() + ", " + self.size.__str__() + ", ")


class PIT:
    def __init__(self):
        self.pit = dict()  # key: packet_name, value: time

    def __str__(self):
        for key, value in self.pit.items():
            print(key + ", " + value.__str__(), end=",")
        print(" ")

    def pit_has_name(self, name: str):
        if name in self.pit:
            return True
        else:
            return False

    def get_pit_entry(self, name: str):
        return self.pit[name]

    def add_to_pit(self, name: str, t: int):
        self.pit[name] = t

    def del_from_pit(self, name: str):
        self.pit.pop(name)

    def update_pit_times(self, env: Environment):
        self.pit = {key: val for key, val in self.pit.items() if self.get_pit_entry(key) > env.now}


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
        self.chrhpc = 0  # cache hit ratio for high priority content
        self.chrlpc = 0  # cache hit ratio for low priority content
        self.cmr = 0  # cache miss ratio

        self.p = 0  # Target size for the list T1

        # Random structure
        self.random_struct = dict()

        # LFU structure
        self.min_f = 1
        self.freq_map = defaultdict(LinkedHashSet)  # frequency:LinkedHashSet
        self.cache = {}  # key:(value, frequency)

        # LRU structure
        self.lru_dict = OrderedDict()

        # ARC structure
        # L1: only once recently
        self.t1 = Deque()  # T1: recent cache entries
        self.b1 = Deque()  # B1: ghost entries recently evicted from the T1 cache
        # L2: at least twice recently
        self.t2 = Deque()  # T2: frequent entries
        self.b2 = Deque()  # B2: ghost entries recently evicted from the T2 cache

        # disk structure
        self.submission_queue = []
        self.submission_queue_max_size = 64

    def register_listener(self, listener: "Policy"):
        self.listeners += [listener]

    def read_packet(self, env: Environment, packet):
        for listener in self.listeners:
            env.process(listener.on_packet_access(env, packet, False))

    def write_packet(self, env: Environment, packet, cause=None):
        for listener in self.listeners:
            env.process(listener.on_packet_access(env, packet, True))

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

    def index_has_name(self, name: str):
        if name in self.index:
            return True
        else:
            return False

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
