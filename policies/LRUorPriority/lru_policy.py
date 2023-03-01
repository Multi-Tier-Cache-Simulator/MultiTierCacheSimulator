import math
from collections import OrderedDict

from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class DISKLRUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)

        self.c = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

        self.lru_dict = OrderedDict()

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool, cause=None):
        print('%s arriving at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
        if self.c == 0:
            print("cache units == %s" % self.c)
            return

        if is_write:
            if len(self.lru_dict) >= self.c:
                lru_name, lru_old = self.lru_dict.popitem(last=False)
                # index update
                yield env.process(self.forwarder.index.del_packet_from_cs(lru_name))
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= lru_old.size
                print("evict from disk %s" % lru_old.name)

            self.lru_dict[packet.name] = packet

            # index update
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))

            # increment number of writes
            self.tier.used_size += packet.size
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1

        elif packet.name in self.lru_dict:
            self.lru_dict.move_to_end(packet.name)  # moves it at the end

            # increment number of reads
            self.tier.number_of_reads += 1

            # increment number of writes
            self.tier.number_of_write += 1

        with res[1].request() as req:
            yield req
            print('%s starting at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
            if is_write:
                # writing
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            elif packet.name in self.lru_dict:
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                # reading
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp
                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
                # writing
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            res[1].release(req)
            print(self.lru_dict.keys().__str__())
            self.forwarder.index.__str__()
            self.forwarder.index.__str__(what="Ghost")
            print('%s leaving the resource at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))

    def prefetch_packet(self, env: Environment, packet: Packet):
        print("prefetch packet from %s" % self.tier.name)
        if packet.name in self.lru_dict:
            del self.lru_dict[packet.name]

            # index update
            yield env.process(self.forwarder.index.del_packet_from_cs(packet.name))

            # evict data
            self.tier.number_of_prefetching_from_this_tier += 1
            self.tier.used_size -= packet.size
            self.tier.number_of_packets -= 1
