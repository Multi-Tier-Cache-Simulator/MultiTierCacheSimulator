from collections import OrderedDict
from policies.policy import Policy
from storage_structures import StorageManager, Tier
from simpy.core import Environment


class LRUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.lru_file_dict = OrderedDict()

    def on_packet_access(self, timestamp: int, name: str, size: int, priority: str, isWrite: bool):
        if isWrite:
            print("Writing \"" + name.__str__() + "\" to " + self.tier.name.__str__())
            self.lru_file_dict[name] = name
            self.storage.index.update_packet_tier(name, self.tier)
            self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
            self.tier.number_of_packets = +1
            self.tier.used_size += size
        else:
            print("Reading \"" + name.__str__() + "\" from " + self.tier.name.__str__())
            self.tier.time_spent_reading += self.tier.latency + size / self.tier.throughput
            self.lru_file_dict.move_to_end(name)  # moves it at the end
