from policies.policy import Policy
from storage_structures import StorageManager, Tier
from simpy.core import Environment


class LRUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)

    def on_packet_access(self, tstart_tlast: int, name: str, size: int, priority: str, isWrite: bool,
                         drop="n"):
        print("==========================")
        print("disk LRU = " + self.tier.lru_dict.items().__str__())
        print("index.keys() = " + self.storage.index.index.keys().__str__())
        print("disk index = " + self.storage.index.index.__str__())
        print("==========================")
        if isWrite:
            print("Writing \"" + name.__str__() + "\" to " + self.tier.name.__str__())
            for key, value in reversed(self.tier.lru_dict.items()):
                if value.lower() == drop.lower():
                    print("Dropping a packet with " + drop + " priority")
                    self.tier.lru_dict.pop(key)
                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= size
                    # index update
                    self.storage.index.del_packet(key)
                    break
            self.tier.lru_dict[name] = priority
            self.tier.lru_dict.move_to_end(name)  # moves it at the end
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

            self.tier.lru_dict.move_to_end(name)  # moves it at the end
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
