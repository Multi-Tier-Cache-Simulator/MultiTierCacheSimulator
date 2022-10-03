import math
import numpy
from policies.policy import Policy
from storage_structures import StorageManager, Tier, Packet
from simpy.core import Environment


class DRAMLRUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / storage.slot_size)

    def on_packet_access(self, tstart_tlast: int, packet: Packet, isWrite: bool,
                         drop="n"):
        print("dram LRU length = " + len(self.tier.lru_dict).__str__())
        print("index length before = " + len(self.storage.index.index).__str__())
        # print("dram LRU = " + self.tier.lru_dict.items().__str__())
        # print(self.storage.index.__str__())
        if isWrite:
            if packet.name in self.tier.lru_dict.keys():
                print("data already in cache")
                return

            print("Writing to " + self.tier.name.__str__())
            p1 = 0.1
            p2 = 0.2
            # free space if capacity full
            if len(self.tier.lru_dict) >= self.nb_packets_capacity:
                key, old = reversed(self.tier.lru_dict.popitem())
                print(old.__str__() + " evicted from " + self.tier.name.__str__())
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= key.size
                # index update
                self.storage.index.del_packet(old)
                # store the removed packet from dram in disk ?
                x = numpy.random.uniform(low=0.0, high=1.0, size=None)
                print("index length after = " + len(self.storage.index.index).__str__())
                if x < p1:
                    # drop current packet
                    print("drop " + old.__str__())
                if p1 < x < p2:
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        print("hpc-move data to disk " + old)
                        self.storage.tiers[target_tier_id].write_packet(tstart_tlast, key,
                                                                        "h")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")
                if x >= p2:
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        print("lpc-move data to disk " + old)
                        self.storage.tiers[target_tier_id].write_packet(tstart_tlast, key,
                                                                        "l")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")

            self.tier.lru_dict[packet.name] = packet
            self.tier.lru_dict.move_to_end(packet.name)  # moves it at the end
            # index update
            self.storage.index.update_packet_tier(packet.name, self.tier)
            # time
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            # write data
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size
            print("index length after = " + len(self.storage.index.index).__str__())
        else:
            print("cache hit")
            self.tier.lru_dict.move_to_end(packet.name)  # moves it at the end
            self.tier.chr += 1  # chr
            # time
            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
            # read a data
            self.tier.number_of_reads += 1
