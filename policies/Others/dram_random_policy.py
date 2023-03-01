import math
import random
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class DRAMRandPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.name = "DRAM_Rand"
        # self.nb_packets_capacity = 3
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)
        self.random_struct = {}

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s' % (self.tier.name, (env.now)))
        with res[0].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, (env.now)))
            if is_write:
                # free space if capacity full
                if len(self.random_struct) >= self.nb_packets_capacity:
                    # remove a random key from the cache
                    removed_key = random.choice(list(self.random_struct.keys()))
                    old = self.random_struct.get(removed_key)

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
                        if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                            print("move data to disk " + old.name)
                            self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')

                        # disk is overloaded --> drop packet
                        else:
                            print("drop packet" + old.name)
                    except:
                        print("no other tier")

                    self.random_struct.pop(removed_key)

                yield env.timeout(
                    self.tier.latency + packet.size / self.tier.write_throughput)

                self.random_struct[packet.name] = packet

                # index update
                self.forwarder.index.update_packet_tier(packet.name, self.tier)

                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # increment number of packets and used size
                self.tier.used_size += packet.size
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1
            else:
                if packet.name in self.random_struct:
                    yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)

                    # update time spent reading
                    if packet.priority == 'l':
                        self.tier.low_p_data_retrieval_time += (env.now) - packet.timestamp
                    else:
                        self.tier.high_p_data_retrieval_time += (env.now) - packet.timestamp

                    self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

                    # increment number of reads
                    self.tier.number_of_reads += 1
                else:
                    raise ValueError(f"Key {packet.name} not found in cache.")
            res[0].release(req)
            print('%s leaving the resource at %s' % (self.tier.name, (env.now)))
