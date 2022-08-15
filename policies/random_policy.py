import math
import random
from policies.policy import Policy
from storage_structures import StorageManager, Tier
from simpy.core import Environment


class RandPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / 16777216)

    def on_packet_access(self, tstart_tlast: int, name: str, size: int, priority: str, isWrite: bool,
                         drop="n"):
        print("==========================")
        print("disk random = " + self.tier.random_struct.__str__())
        print("disk index = " + self.storage.index.index.__str__())
        print("==========================")
        if isWrite:
            print("Writing \"" + name.__str__() + "\" to " + self.tier.name.__str__())
            if len(self.tier.random_struct) == self.nb_packets_capacity:
                old = self.tier.random_struct.pop(random.randrange(len(self.tier.random_struct)))
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= size
                # index update
                self.storage.index.del_packet(old)

            self.tier.random_struct.append(name)
            # index update
            self.storage.index.update_packet_tier(name, self.tier)
            # time
            if tstart_tlast > self.tier.last_completion_time:
                self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
                self.tier.last_completion_time = self.tier.latency + size / self.tier.throughput
            else:
                self.tier.time_spent_writing += self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                + size / self.tier.throughput
                self.tier.last_completion_time = self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                 + size / self.tier.throughput
            # write data
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += size
        else:
            print("Reading \"" + name.__str__() + "\" from " + self.tier.name.__str__())
            self.tier.chr += 1  # chr
            # time
            if tstart_tlast > self.tier.last_completion_time:
                self.tier.time_spent_reading += self.tier.latency + size / self.tier.throughput
                self.tier.last_completion_time = self.tier.latency + size / self.tier.throughput
            else:
                self.tier.time_spent_reading += self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                + size / self.tier.throughput
                self.tier.last_completion_time = self.tier.last_completion_time - tstart_tlast + self.tier.latency \
                                                 + size / self.tier.throughput
            # read a data
            self.tier.number_of_reads += 1
