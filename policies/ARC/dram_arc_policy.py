import math

from simpy.core import Environment

from common.deque import Deque
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder_structures.forwarder import Forwarder
from policies.policy import Policy


class DRAMARCPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)

        self.c = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

        self.t1 = Deque()  # T1: recent cache entries
        self.t2 = Deque()  # T2: frequent entries

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool, cause=None):
        print('%s arriving at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))

        if packet.name in self.t1 or packet.name in self.t2:
            # increment number of reads
            self.tier.number_of_reads += 1
        else:
            raise ValueError(f"Key {packet.name} not found in cache.")

        with res[self.forwarder.tiers.index(self.tier)].request() as req:
            yield req
            print('%s starting at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
            if packet.name in self.t1 or packet.name in self.t2:
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                # reading
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp
                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
            else:
                raise ValueError(f"Key {packet.name} not found in cache.")

            self.t1.__str__()
            self.t2.__str__()
            self.forwarder.index.__str__()
            self.forwarder.index.__str__(what="Ghost")
            print('%s leaving the resource at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))

    def on_packet_access_t1(self, env, res, packet: Packet, index=-1):
        print('%s arriving at %s' % (self.tier.name, env.now))

        # if cache full, send data to disk
        if len(self.t1) + len(self.t2) >= self.c:
            if len(self.t1) >= self.c:
                yield env.process(self.send_to_next_level_t1(env, res))
            # move from T2 dram to T2 disk
            elif self.t2:
                yield env.process(self.send_to_next_level_t2(env, res))
            else:
                yield env.process(self.send_to_next_level_t1(env, res))

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

    def on_packet_access_t2(self, env, res, packet: Packet, index=-1):
        print('%s arriving at %s' % (self.tier.name, env.now))

        if len(self.t1) + len(self.t2) >= self.c:
            if len(self.t1) >= self.c:
                yield env.process(self.send_to_next_level_t1(env, res))
            # move from T2 dram to T2 disk
            elif self.t2:
                yield env.process(self.send_to_next_level_t2(env, res))
            else:
                yield env.process(self.send_to_next_level_t1(env, res))

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

    def send_to_next_level_t1(self, env: Environment, res):
        name, packet = self.t1.get_without_pop()
        self.t1.pop()

        self.forwarder.get_last_tier().number_of_eviction_to_this_tier += 1
        self.tier.number_of_eviction_from_this_tier += 1
        self.tier.number_of_packets -= 1
        self.tier.used_size -= packet.size

        print('send packet %s from t1 dram to t1 disk' % packet.name)
        try:
            target_tier_id = self.forwarder.tiers.index(self.tier) + 1
            # Disk is free
            if len(res[target_tier_id].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                print("evict from t1 to disk %s" % packet.name)
                yield env.process(self.forwarder.tiers[target_tier_id].write_packet_t1(env, res, packet, index=-1,
                                                                                       cause='eviction'))
            # disk is overloaded --> drop packet
            else:
                print("drop packet %s" % packet.name)
        except Exception as e:
            print("error : %s" % e)

    def send_to_next_level_t2(self, env: Environment, res):
        name, packet = self.t2.get_without_pop()
        self.t2.pop()

        self.forwarder.get_last_tier().number_of_eviction_to_this_tier += 1
        self.tier.number_of_eviction_from_this_tier += 1
        self.tier.number_of_packets -= 1
        self.tier.used_size -= packet.size

        print('send packet %s from t2 dram to t2 disk' % packet.name)
        try:
            target_tier_id = self.forwarder.tiers.index(self.tier) + 1
            # Disk is free
            if len(res[target_tier_id].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                print("evict from t2 to disk %s" % packet.name)
                yield env.process(
                    self.forwarder.tiers[target_tier_id].write_packet_t2(env, res, packet, index=-1,
                                                                         cause='eviction'))
            # disk is overloaded --> drop packet
            else:
                print("drop packet %s" % packet.name)
        except Exception as e:
            print("error : %s" % e)
