import math
from policies.policy import Policy
from storage_structures import StorageManager, Tier, Packet
from simpy.core import Environment


class LRUPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / storage.slot_size)

    def on_packet_access(self, tstart_tlast: int, packet: Packet, isWrite: bool,
                         drop="n"):
        print("disk LRU length = " + len(self.tier.lru_dict).__str__())
        print("index length before = " + len(self.storage.index.index).__str__())
        # print("capacity = "+self.nb_packets_capacity.__str__())
        # print("disk used size bafore = "+self.tier.used_size.__str__())
        # print("disk LRU = " + self.tier.lru_dict.items().__str__())
        # print(self.storage.index.__str__())
        if isWrite:
            if packet.name in self.tier.lru_dict:
                print("data already in cache" + packet.name)
                return

            print("Writing to " + self.tier.name.__str__())
            if len(self.tier.lru_dict) >= self.nb_packets_capacity:
                for key, value in reversed(self.tier.lru_dict.items()):
                    if value.lower() == drop.lower():
                        print(key.__str__() + " evicted from " + self.tier.name.__str__())
                        self.tier.lru_dict.pop(key)
                        # evict data
                        self.tier.number_of_eviction_from_this_tier += 1
                        self.tier.number_of_packets -= 1
                        self.tier.used_size -= value.size
                        # index update
                        self.storage.index.del_packet(key)
                        print("index length after = " + len(self.storage.index.index).__str__())
                        break
            self.tier.lru_dict[packet.name] = packet
            self.tier.lru_dict.move_to_end(packet.name)  # moves it at the end
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
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size
            print("index length after = " + len(self.storage.index.index).__str__())
        else:
            print("cache hit")
            self.tier.lru_dict.move_to_end(packet.name)  # moves it at the end
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

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from disk " + self.tier.name.__str__())
        self.tier.lru_dict.pop(packet.name)
        self.tier.number_of_prefetching_from_this_tier += 1
        self.tier.number_of_packets -= 1
        self.tier.used_size -= packet.size
        self.storage.index.del_packet(packet.name)
