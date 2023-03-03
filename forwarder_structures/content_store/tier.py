from simpy.core import Environment


class Tier:
    def __init__(self, name: str, max_size: int, granularity: int, latency: float, read_throughput: float,
                 write_throughput: float, target_occupation: float = 1.0):
        """""
        :param name: name of the tier
        :param max_size: octets
        :param granularity: block size
        :param latency: nanoseconds
        :param read_throughput: o/nanoseconds
        :param write_throughput: o/nanoseconds
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
        self.strategies = []
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

        self.penalty = 0  # eviction penalty

        self.submission_queue_max_size = 64  # disk structure

    def register_strategy(self, strategy: "Policy"):
        self.strategies += [strategy]

    def read_packet(self, env: Environment, res, packet):
        for strategy in self.strategies:
            yield env.process(strategy.on_packet_access(env, res, packet, False))

    def write_packet(self, env, res, packet, cause=None):
        for strategy in self.strategies:
            yield env.process(strategy.on_packet_access(env, res, packet, True))
        if cause is not None:
            if cause == "eviction":
                self.number_of_eviction_to_this_tier += 1
            elif cause == "prefetching":
                self.number_of_prefetching_to_this_tier += 1
            else:
                raise RuntimeError(f'Unknown cause {cause}. Expected "eviction", "prefetching" or None')

    def write_packet_t1(self, env, res, packet, index=None, cause=None):
        for strategy in self.strategies:
            yield env.process(strategy.on_packet_access_t1(env, res, packet, index))
        if cause is not None:
            if cause == "eviction":
                self.number_of_eviction_to_this_tier += 1
            elif cause == "prefetching":
                self.number_of_prefetching_to_this_tier += 1
            else:
                raise RuntimeError(f'Unknown cause {cause}. Expected "eviction", "prefetching" or None')

    def write_packet_t2(self, env, res, packet, is_write, index=None, cause=None):
        for strategy in self.strategies:
            yield env.process(strategy.on_packet_access_t2(env, res, packet, is_write, index))
        if cause is not None:
            if cause == "eviction":
                self.number_of_eviction_to_this_tier += 1
            elif cause == "prefetching":
                self.number_of_prefetching_to_this_tier += 1
            else:
                raise RuntimeError(f'Unknown cause {cause}. Expected "eviction", "prefetching" or None')

    def prefetch_packet(self, env, packet):
        for strategy in self.strategies:
            yield env.process(strategy.prefetch_packet(env, packet))
