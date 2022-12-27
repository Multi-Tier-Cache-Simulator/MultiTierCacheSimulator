import math
from decimal import Decimal
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class LRUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s' % (self.tier.name, Decimal(env.now)))
        with res[1].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, Decimal(env.now)))
            # print('Queue size: %s' % len(res[1].queue))
            # print(self.forwarder.index.__str__())
            # print(self.forwarder.index.__str__(what='queues'))
            if is_write:
                if len(self.tier.lru_dict) > self.nb_packets_capacity:
                    old, name = reversed(self.tier.lru_dict.popitem())
                    print(name + " evicted from " + self.tier.name)

                    # index update
                    self.forwarder.index.del_packet_from_cs(name)

                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old.size

                yield env.timeout(packet.size / self.tier.write_throughput)
                self.tier.lru_dict[packet.name] = packet
                self.tier.lru_dict.move_to_end(packet.name)  # moves it at the end

                # index update
                self.forwarder.index.update_packet_tier(packet.name, self.tier)

                # time
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # write data
                self.tier.used_size += packet.size
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1

            else:
                yield env.timeout(packet.size / self.tier.read_throughput)
                self.tier.lru_dict.move_to_end(packet.name)  # moves it at the end

                # time
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp

                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

                # read a data
                self.tier.number_of_reads += 1
            print('%s leaving the resource at %s' % (self.tier.name, Decimal(env.now)))

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from disk " + self.tier.name.__str__())
        self.tier.lru_dict.pop(packet.name)
        self.tier.number_of_prefetching_from_this_tier += 1
        self.tier.number_of_packets -= 1
        self.tier.used_size -= packet.size
        self.forwarder.index.del_packet_from_cs(packet.name)
