import math
from policies.policy import Policy
from storage_structures import StorageManager, Tier, Packet
from simpy.core import Environment


class LFUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.__capa = math.trunc(self.tier.max_size * self.tier.target_occupation / storage.slot_size)

    def on_packet_access(self, tstart_tlast: int, packet: Packet, isWrite: bool,
                         drop="n"):
        print("disk LFU length = " + len(self.tier.key_to_freq).__str__())
        print("index length before = " + len(self.storage.index.index).__str__())
        # print("disk LFU = " + self.tier.key_to_freq.items().__str__())
        # print(self.storage.index.__str__())
        if isWrite:
            if self.__capa <= 0:
                print("error cache has no memory")
                return
            if packet.name in self.tier.key_to_freq:
                print("data already in cache")
                return

            print("Writing to " + self.tier.name.__str__())
            # key not in key_to_freq and size == capacity --> free space
            if packet.name not in self.tier.key_to_freq and self.tier.number_of_packets == self.__capa:
                old, oldp = list(self.tier.freq_to_nodes[self.tier.min_freq].items())[0]
                print(old.__str__() + " evicted from " + self.tier.name.__str__())
                del self.tier.key_to_freq[self.tier.freq_to_nodes[self.tier.min_freq].popitem(last=False)[0]]
                if not self.tier.freq_to_nodes[self.tier.min_freq]:
                    del self.tier.freq_to_nodes[self.tier.min_freq]
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= oldp.size
                # index update
                self.storage.index.del_packet(old)
                print("index length after = " + len(self.storage.index.index).__str__())

            self.update(packet, drop)
            # index update
            self.storage.index.update_packet_tier(packet.name, self.tier)
            # time
            if tstart_tlast > self.tier.last_completion_time:
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
                self.tier.last_completion_time = self.tier.latency + packet.size / self.tier.write_throughput
            else:
                self.tier.time_spent_writing += self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                + packet.size / self.tier.write_throughput
                self.tier.last_completion_time = self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                 + packet.size / self.tier.write_throughput
            # write data
            self.tier.number_of_write += 1
            self.tier.number_of_packets += 1
            self.tier.used_size += packet.size
            print("index length after = " + len(self.storage.index.index).__str__())
        else:  # get
            if packet.name not in self.tier.key_to_freq:
                print("data not in cache")
                return -1
            print("cache hit")
            self.update(packet, drop)

            self.tier.chr += 1  # chr
            # time
            if tstart_tlast > self.tier.last_completion_time:
                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
                self.tier.last_completion_time = self.tier.latency + packet.size / self.tier.read_throughput
            else:
                self.tier.time_spent_reading += self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                + packet.size / self.tier.read_throughput
                self.tier.last_completion_time = self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                 + packet.size / self.tier.read_throughput
            # read a data
            self.tier.number_of_reads += 1

    def update(self, packet: Packet, drop):
        freq = 0
        if packet.name in self.tier.key_to_freq:
            freq = self.tier.key_to_freq[packet.name]
            del self.tier.freq_to_nodes[freq][packet.name]
            if not self.tier.freq_to_nodes[freq]:
                del self.tier.freq_to_nodes[freq]
                if self.tier.min_freq == freq:
                    self.tier.min_freq += 1

        freq += 1
        self.tier.min_freq = min(self.tier.min_freq, freq)
        self.tier.key_to_freq[packet.name] = freq
        self.tier.freq_to_nodes[freq][packet.name] = packet

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from disk " + self.tier.name.__str__())
        if packet.name in self.tier.key_to_freq:
            freq = self.tier.key_to_freq[packet.name]
            del self.tier.key_to_freq[packet.name]
            del self.tier.freq_to_nodes[freq][packet.name]
            if not self.tier.freq_to_nodes[freq]:
                del self.tier.freq_to_nodes[freq]
            self.tier.number_of_prefetching_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= packet.size
            self.storage.index.del_packet(packet.name)
