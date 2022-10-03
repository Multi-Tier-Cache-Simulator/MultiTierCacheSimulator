import math
import numpy
from policies.policy import Policy
from storage_structures import StorageManager, Tier, Packet
from simpy.core import Environment


class DRAMLFUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.__capa = math.trunc(self.tier.max_size * self.tier.target_occupation / storage.slot_size)

    def on_packet_access(self, tstart_tlast: int, packet: Packet, isWrite: bool,
                         drop="n"):
        print("dram LFU length = " + len(self.tier.key_to_freq).__str__())
        print("index length before = " + len(self.storage.index.index).__str__())
        # print("dram LFU = " + self.tier.key_to_freq.items().__str__())
        # print(self.storage.index.__str__())
        if isWrite:  # put
            if self.__capa <= 0:
                print("error cache has no memory")
                return
            if packet.name in self.tier.key_to_freq:
                print("data already in dram")
                return
            # print("Writing \"" + name.__str__() + "\" to " + self.tier.name.__str__())
            p1 = 0.1
            p2 = 0.2
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
                self.tier.used_size -= packet.size
                # index update
                self.storage.index.del_packet(old)
                x = numpy.random.uniform(low=0.0, high=1.0, size=None)
                print("index length after = " + len(self.storage.index.index).__str__())
                if x < p1:
                    # drop current packet
                    print("drop " + old.__str__())
                if p1 < x < p2:
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        print("hpc-move data to disk " + old)
                        self.storage.tiers[target_tier_id].write_packet(tstart_tlast, oldp,
                                                                        "h")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")
                if x > p2:
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        print("lpc-move data to disk " + old)
                        self.storage.tiers[target_tier_id].write_packet(tstart_tlast, oldp,
                                                                        "l")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")
            self.update(packet, drop)

            # index update
            self.storage.index.update_packet_tier(packet.name, self.tier)
            # time
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            self.tier.number_of_packets += 1
            self.tier.used_size += packet.size
            # write data
            self.tier.number_of_write += 1
            print("index length after = " + len(self.storage.index.index).__str__())
        else:  # get
            if packet.name not in self.tier.key_to_freq:
                print("data not in cache")
                return -1
            print("Reading \"" + packet.name.__str__() + "\" from " + self.tier.name.__str__())
            self.update(packet, drop)

            self.tier.chr += 1  # chr
            # time
            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
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
