import math
from collections import OrderedDict

from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class DRAMLRUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)

        self.c = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

        self.lru_dict = OrderedDict()

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving the resource at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
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

                print("evict to disk %s" % lru_old.name)
                try:
                    target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                    # data is important or Disk is free
                    if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                        print("evict to disk %s" % lru_name)
                        yield env.process(
                            self.forwarder.tiers[target_tier_id].write_packet(env, res, lru_old, cause='eviction'))
                        # disk is overloaded --> drop packet
                    else:
                        print("drop packet %s" % lru_name)
                except Exception as e:
                    print("error : %s" % e)

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

        with res[0].request() as req:
            yield req
            print('%s starting at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
            if is_write:
                # writing
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            elif packet.name in self.lru_dict:
                # reading
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp
                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
                # writing
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            else:
                raise ValueError(f"Key {packet.name} not found in cache.")
            res[0].release(req)
            print(self.lru_dict.keys().__str__())
            self.forwarder.index.__str__()
            self.forwarder.index.__str__(what="Ghost")
            print('%s leaving the resource at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
