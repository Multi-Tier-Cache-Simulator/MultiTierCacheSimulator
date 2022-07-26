from policies.policy import Policy
from storage_structures import StorageManager, Tier
from simpy.core import Environment


class LFUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.__capa = 71

    def on_packet_access(self, timestamp: int, tstart_tlast: int, name: str, size: int, priority: str, isWrite: bool,
                         drop="n"):
        if isWrite:
            print("==================")
            if self.__capa <= 0:
                print("cache full")
                return

            # key not in key_to_freq and size == capacity --> free space
            if name not in self.tier.key_to_freq and self.tier.number_of_packets == self.__capa:
                print("key not in self.__key_to_freq and == self.__capa")
                del self.tier.key_to_freq[self.tier.freq_to_nodes[self.tier.min_freq].popitem(last=False)[0]]
                if not self.tier.freq_to_nodes[self.tier.min_freq]:
                    del self.tier.freq_to_nodes[self.tier.min_freq]
                self.tier.number_of_packets -= 1
            print("update from put")
            self.update(timestamp, tstart_tlast, name, size, priority, drop)
        else:
            print("==================")
            if name not in self.tier.key_to_freq:
                print("data not in cache")
                return -1
            print("data in cache")
            self.tier.chr += 1
            priority = self.tier.freq_to_nodes[self.tier.key_to_freq[name]][name]
            print(priority)
            self.update(timestamp, tstart_tlast, name, size, priority, drop)

    def update(self, timestamp, tstart_tlast, name, size, priority, drop):
        print("==================")
        freq = 0
        if name in self.tier.key_to_freq:
            freq = self.tier.key_to_freq[name]
            del self.tier.freq_to_nodes[freq][name]
            if not self.tier.freq_to_nodes[freq]:
                del self.tier.freq_to_nodes[freq]
                if self.tier.min_freq == freq:
                    self.tier.min_freq += 1
            self.tier.number_of_packets -= 1

        freq += 1
        self.tier.min_freq = min(self.tier.min_freq, freq)
        self.tier.key_to_freq[name] = freq
        self.tier.freq_to_nodes[freq][name] = priority
        self.tier.number_of_packets += 1
        print("__key_to_freq = " + self.tier.key_to_freq.__str__())
        print("__freq_to_nodes = " + self.tier.freq_to_nodes.__str__())
        # index update
        self.storage.index.update_packet_tier(name, self.tier)
        # time
        self.tier.time_spent_writing += abs(
            self.tier.last_completion_time - tstart_tlast + self.tier.latency + size / self.tier.throughput)
        self.tier.last_completion_time = abs(
            self.tier.last_completion_time - tstart_tlast + self.tier.latency + size / self.tier.throughput)
        # write data
        self.tier.number_of_write += 1
        self.tier.used_size += size

