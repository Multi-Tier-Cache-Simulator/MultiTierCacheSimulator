import math
from collections import OrderedDict
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class LRUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.name = "LRU"
        # self.nb_packets_capacity = 3
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)
        self.lru_dict = OrderedDict()

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
        print(self.forwarder.index.__str__())
        if is_write:
            # if the packet is not already in cache, prepare its insertion
            if packet.name not in self.lru_dict:
                if len(self.lru_dict) >= self.nb_packets_capacity:
                    name, old = self.lru_dict.popitem(last=False)

                    # index update
                    self.forwarder.index.del_packet_from_cs(name)

                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old.size

                    print("%s evict from DISK " % old.name)

                self.lru_dict[packet.name] = packet

                # increment number of writes
                self.tier.used_size += packet.size
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1

            # index update
            self.forwarder.index.update_packet_tier(packet.name, self.tier)

        print(self.forwarder.index.__str__())
        with res[1].request() as req:
            yield req
            print('%s starting at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
            if is_write:
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)

                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            else:
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)

                if packet.name in self.lru_dict:
                    yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)

                    self.lru_dict.move_to_end(packet.name)  # moves it at the end

                    # update time spent writing
                    self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                    # increment number of writes
                    self.tier.number_of_write += 1

                # update time spent reading
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp

                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

                # increment number of reads
                self.tier.number_of_reads += 1

            res[1].release(req)
            print(self.forwarder.index.__str__())
            print('%s leaving the resource at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from " + self.tier.name.__str__())
        if packet.name in self.lru_dict:
            del self.lru_dict[packet.name]

            # index update
            self.forwarder.index.del_packet_from_cs(packet.name)

            # evict data
            self.tier.number_of_prefetching_from_this_tier += 1
            self.tier.used_size -= packet.size
            self.tier.number_of_packets -= 1
