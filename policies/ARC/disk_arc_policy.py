import math

from common.deque import Deque
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class DISKARCPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)

        self.c = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

        self.p = 0  # Target size for the list T1
        self.t1 = Deque()  # T1: recent cache entries
        self.t2 = Deque()  # T2: frequent entries

    def on_packet_access_t1(self, env: Environment, res, packet: Packet, index=None):
        print('%s arriving at %s for %s' % (self.tier.name, env.now, packet.name))

        if index:
            self.t1.append_by_index(index, packet.name, packet)
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
        else:
            self.t1.append_left(packet.name, packet)
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))

        # increment number of writes
        self.tier.number_of_packets += 1
        self.tier.number_of_write += 1
        self.tier.used_size += packet.size

        with res[self.forwarder.tiers.index(self.tier)].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, env.now))

            # writing
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            res[self.forwarder.tiers.index(self.tier)].release(req)

            self.t1.__str__()
            self.t2.__str__()
            self.forwarder.index.__str__()
            self.forwarder.index.__str__(what="Ghost")
            print('%s leaving the resource at %s' % (self.tier.name, env.now))
            return

    def on_packet_access_t2(self, env: Environment, res, packet: Packet, is_write: bool, index=None):
        print('%s arriving at %s for %s' % (self.tier.name, env.now, packet.name))

        if index:
            self.t2.append_by_index(index, packet.name, packet)
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
        else:
            self.t2.append_left(packet.name, packet)
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))

        # increment number of writes
        self.tier.number_of_packets += 1
        self.tier.number_of_write += 1
        self.tier.used_size += packet.size

        with res[self.forwarder.tiers.index(self.tier)].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, env.now))

            # writing
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            res[self.forwarder.tiers.index(self.tier)].release(req)

            self.t1.__str__()
            self.t2.__str__()
            self.forwarder.index.__str__()
            self.forwarder.index.__str__(what="Ghost")
            print('%s leaving the resource at %s' % (self.tier.name, env.now))
            return
