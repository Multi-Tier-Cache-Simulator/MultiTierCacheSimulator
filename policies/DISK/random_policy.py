import math
import random
from decimal import Decimal
from policies.policy import Policy
from forwarder_structures import Forwarder, Tier, Packet
from simpy.core import Environment


class RandPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s' % (self.tier.name, Decimal(env.now)))
        print('Queue size: %s' % len(res[1].queue))
        with res[1].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, Decimal(env.now)))
            if is_write:
                if len(self.tier.random_struct) > self.nb_packets_capacity:
                    old = self.tier.random_struct.pop(
                        list(self.tier.random_struct.keys())[random.randrange(len(self.tier.random_struct))])
                    print(old.name + " evicted from " + self.tier.name)

                    # index update
                    self.forwarder.index.del_packet_from_cs(old.name)

                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old.size

                print("writing " + packet.name + " to " + self.tier.name.__str__())
                yield env.timeout(packet.size / self.tier.write_throughput)
                self.tier.random_struct[packet.name] = packet

                print('=========')
                print("finished writing " + packet.name + " to " + self.tier.name.__str__())

                # index update
                self.forwarder.index.update_packet_tier(packet.name, self.tier)

                # time
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # write data
                self.tier.used_size += packet.size
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1

            else:
                print("reading " + packet.name + " to " + self.tier.name.__str__())
                yield env.timeout(packet.size / self.tier.read_throughput)
                print('=========')
                print("finished reading " + packet.name + " to " + self.tier.name.__str__())

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
        del self.tier.random_struct[packet.name]
        self.tier.number_of_prefetching_from_this_tier += 1
        self.tier.number_of_packets -= 1
        self.tier.used_size -= packet.size
        self.forwarder.index.del_packet_from_cs(packet.name)
