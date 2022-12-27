import math
import random
from decimal import Decimal
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class DRAMRandPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s' % (self.tier.name, Decimal(env.now)))
        with res[0].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, Decimal(env.now)))
            if is_write:
                # free space if capacity full
                if len(self.tier.random_struct) > self.nb_packets_capacity:
                    old = self.tier.random_struct.pop(random.choice(list(self.tier.random_struct.keys())))
                    print(old.name + " evicted from " + self.tier.name)

                    # index update
                    self.forwarder.index.del_packet_from_cs(old.name)

                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old.size

                    # store the removed packet from dram in disk ?
                    try:
                        target_tier_id = self.forwarder.tiers.index(self.tier) + 1

                        # data is important or Disk is free
                        if len(res[1].queue) != self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                            print("move data to disk " + old.name)
                            self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')

                        # disk is overloaded --> drop packet
                        else:
                            print("drop packet" + old.name)
                    except:
                        print("no other tier")
                yield env.timeout(
                    self.tier.latency + packet.size / self.tier.write_throughput)
                self.tier.random_struct[packet.name] = packet

                # index update
                self.forwarder.index.update_packet_tier(packet.name, self.tier)

                # time
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # write data
                self.tier.used_size += packet.size
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1

            else:
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                # time
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

                # read a data
                self.tier.number_of_reads += 1
            print('%s leaving the resource at %s' % (self.tier.name, Decimal(env.now)))
