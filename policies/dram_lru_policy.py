import numpy

from policies.policy import Policy
from storage_structures import StorageManager, Tier
from simpy.core import Environment


class DRAMLRUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)

    def on_packet_access(self, timestamp: int, tstart_tlast: int, name: str, size: int, priority: str, isWrite: bool,
                         drop="n"):
        print("==========================")
        print("dram = " + self.tier.lru_dict.items().__str__())
        print("==========================")
        if isWrite:
            print("Writing \"" + name.__str__() + "\" to " + self.tier.name.__str__())
            p1 = 0.5
            if len(self.tier.lru_dict) >= 71:
                print("total > 71")
                key, old = reversed(self.tier.lru_dict.popitem())
                print(old.__str__() + " evicted from Dram")
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= size
                # index update
                self.storage.index.del_packet(old)
                # store the removed packet from t2 in disk ?
                x = numpy.random.uniform(low=0.0, high=1.0, size=None)
                if x < p1:
                    print("migrate " + old.__str__() + " to disk and drop HPC")
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        self.storage.tiers[target_tier_id].write_packet(timestamp, tstart_tlast, old, size, priority,
                                                                        "h")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")
                    return
                if x >= p1:
                    print("migrate " + old.__str__() + " to disk and drop LPC")
                    target_tier_id = self.storage.tiers.index(self.tier) + 1
                    try:
                        self.storage.tiers[target_tier_id].write_packet(timestamp, tstart_tlast, old, size, priority,
                                                                        "l")
                        self.storage.tiers[target_tier_id].number_of_eviction_to_this_tier += 1
                    except:
                        print("no other tier")
                    return

            self.tier.lru_dict[name] = priority
            self.tier.lru_dict.move_to_end(name)  # moves it at the end
            # index update
            self.storage.index.update_packet_tier(name, self.tier)
            # time
            self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
            self.tier.last_completion_time = self.tier.latency + size / self.tier.throughput
            # write data
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += size
        else:
            print("Reading \"" + name.__str__() + "\" from " + self.tier.name.__str__())

            self.tier.lru_dict.move_to_end(name)  # moves it at the end
            self.tier.chr += 1  # chr
            # time
            self.tier.time_spent_reading += abs(
                self.tier.last_completion_time - tstart_tlast + self.tier.latency + size / self.tier.throughput)
            self.tier.last_completion_time = abs(
                self.tier.last_completion_time - tstart_tlast + self.tier.latency + size / self.tier.throughput)
            # read a data
            self.tier.number_of_reads += 1
