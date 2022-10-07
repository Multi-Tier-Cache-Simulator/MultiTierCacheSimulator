import math
import random
import numpy
from policies.policy import Policy
from storage_structures import StorageManager, Tier, Packet
from simpy.core import Environment


class DRAMRandPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / storage.slot_size)

    def on_packet_access(self, tstart_tlast: int, packet: Packet, isWrite: bool,
                             drop="n"):
        print("dram random length = " + len(self.tier.random_struct).__str__())
        print("index length = " + len(self.storage.index.index).__str__())
        # print("dram random = " + self.tier.random_struct.__str__())
        # print(self.storage.index.__str__())
        if isWrite:
            if packet.name in self.tier.random_struct:
                print("data already in cache")
                return

            print("Writing to " + self.tier.name.__str__())
            p1 = 0.1
            p2 = 0.2
            if len(self.tier.random_struct) >= self.nb_packets_capacity:
                old = self.tier.random_struct.pop(random.choice(list(self.tier.random_struct.keys())))
                print(old.name + " evicted from " + self.tier.name)
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= packet.size
                # index update
                self.storage.index.del_packet(old.name)
                # store the removed packet from dram in disk ?
                x = numpy.random.uniform(low=0.0, high=1.0, size=None)
                print("index length after = " + len(self.storage.index.index).__str__())
                if x < p1:
                    # drop current packet
                    print("drop " + old.name)
                if p1 < x < p2:
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        print("move data to disk " + old)
                        self.storage.tiers[target_tier_id].write_packet(tstart_tlast, old,
                                                                        "h")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")
                if x >= p2:
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        print("move data to disk " + old.name)
                        self.storage.tiers[target_tier_id].write_packet(tstart_tlast, old,
                                                                        "l")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")

            self.tier.random_struct[packet.name] = packet
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
            self.tier.chr += 1  # chr
            # time
            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
            # read a data
            self.tier.number_of_reads += 1
