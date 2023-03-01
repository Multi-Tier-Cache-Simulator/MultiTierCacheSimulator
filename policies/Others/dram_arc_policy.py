import math

from common.deque import Deque
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class DRAMARCPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)

        self.c = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

        self.p = 0  # Target size for the list T1
        self.t1 = Deque()  # T1: recent cache entries
        self.t2 = Deque()  # T2: frequent entries

    def _replace(self, env: Environment, res, packet: Packet):
        in_b2 = yield env.process(self.forwarder.index.packet_in_ghost(packet.name, 'b2'))
        if self.t1 and ((in_b2 and len(self.t1) == self.p) or (len(self.t1) > self.p)):
            name, old = self.t1.get_without_pop()
            print("move from t1 to b1 " + old.name)
            self.t1.pop()
            yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
            yield env.process(self.forwarder.index.update_packet_ghost(old.name, 'b1'))
            # evict data
            self.tier.number_of_eviction_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= old.size
            # store the removed packet from t1 in disk ?
            try:
                target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                # submission queue is not full
                if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                    print("move data to disk " + old.name)
                    self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')
                # disk is overloaded --> drop packet
                else:
                    print("drop packet" + old.name)
            except Exception as e:
                print(e)
                print("no other tier")
        else:
            name, old = self.t2.get_without_pop()
            print("move from t2 to b2 " + old.name)
            self.t2.pop()
            yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
            yield env.process(self.forwarder.index.update_packet_ghost(old.name, 'b2'))

            # evict data
            self.tier.number_of_eviction_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= old.size
            # store the removed packet from t2 in disk ?
            try:
                target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                # submission queue is not full
                if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                    print("move data to disk " + old.name)
                    self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')
                # disk is overloaded --> drop packet
                else:
                    print("drop packet" + old.name)
            except Exception as e:
                print(e)
                print("no other tier")

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool, cause=None):
        print('%s arriving at %s' % (self.tier.name, env.now))
        if self.t1.__contains__(packet.name):
            print('%s starting at %s' % (self.tier.name, env.now))
            self.t1.remove(packet.name)
            self.t2.append_left(packet.name, packet)
            with res[0].request() as req:
                yield req
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                print(packet.name + " cache hit in t1, move to t2")
                # update time spent reading
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp

                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
                # increment number of reads
                self.tier.number_of_reads += 1
                # write
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
                # increment number of writes
                self.tier.number_of_write += 1
                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))

                self.t1.__str__()
                self.t2.__str__()
                self.forwarder.index.__str__()
                self.forwarder.index.__str__(what="Ghost")
                return

        if self.t2.__contains__(packet.name):
            self.t2.remove(packet.name)
            self.t2.append_left(packet.name, packet)
            with res[0].request() as req:
                yield req
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                print(packet.name + " cache hit in t2, move from LRUorPriority to MRU of t2")
                # update time spent reading
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp
                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
                # increment number of reads
                self.tier.number_of_reads += 1
                # write
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
                # increment number of writes
                self.tier.number_of_write += 1
                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))

                self.t1.__str__()
                self.t2.__str__()
                self.forwarder.index.__str__()
                self.forwarder.index.__str__(what="Ghost")
                return

        in_b1 = yield env.process(self.forwarder.index.packet_in_ghost(packet.name, 'b1'))
        if in_b1:
            print(packet.name + " hit in b1, promote to MRU t2")
            len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
            len_b2 = yield env.process(self.forwarder.index.ghost_len('b2'))
            self.p = min(self.c, self.p + max(len_b2 / len_b1, 1))
            yield env.process(self._replace(env, res, packet))
            yield env.process(self.forwarder.index.del_packet_from_ghost(packet.name))
            self.t2.append_left(packet.name, packet)
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
            # increment number of writes
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size

            with res[0].request() as req:
                yield req
                print('%s starting at %s' % (self.tier.name, env.now))
                # write data
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))

                self.t1.__str__()
                self.t2.__str__()
                self.forwarder.index.__str__()
                self.forwarder.index.__str__(what="Ghost")
                return

        in_b2 = yield env.process(self.forwarder.index.packet_in_ghost(packet.name, 'b2'))
        if in_b2:
            print(packet.name + " hit in b2, promote to MRU t2")
            len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
            len_b2 = yield env.process(self.forwarder.index.ghost_len('b2'))
            self.p = max(0, self.p - max(len_b1 / len_b2, 1))
            yield env.process(self._replace(env, res, packet))
            yield env.process(self.forwarder.index.del_packet_from_ghost(packet.name))
            self.t2.append_left(packet.name, packet)
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
            # increment number of writes
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size

            with res[0].request() as req:
                yield req
                print('%s starting at %s' % (self.tier.name, env.now))
                # time
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                self.t1.__str__()
                self.t2.__str__()
                self.forwarder.index.__str__()
                self.forwarder.index.__str__(what="Ghost")
                return

        len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
        if len(self.t1) + len_b1 == self.c:
            print(packet.name + " cache miss in all queues")
            # Case A: L1 (T1 u B1) has exactly c pages.
            if len(self.t1) < self.c:
                print("evict from b1")
                yield env.process(self.forwarder.index.pop_packet_from_ghost('b1'))
                yield env.process(self._replace(env, res, packet))
            else:
                name, old = self.t1.get_without_pop()
                print("evict from t1 " + old.name)
                self.t1.pop()
                yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size
                # store the removed packet from t2 in disk ?
                try:
                    target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                    # submission queue is not full
                    if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                        print("move data to disk " + old.name)
                        self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')
                    # disk is overloaded --> drop packet
                    else:
                        print("drop packet" + old.name)
                except Exception as e:
                    print(e)
                    print("no other tier")
        else:
            len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
            len_b2 = yield env.process(self.forwarder.index.ghost_len('b2'))
            total = len(self.t1) + len_b1 + len(self.t2) + len_b2
            if total >= self.c:
                if total == (2 * self.c):
                    print("evict from b2")
                    yield env.process(self.forwarder.index.pop_packet_from_ghost('b2'))
                yield env.process(self._replace(env, res, packet))

        self.t1.append_left(packet.name, packet)
        yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))

        # increment number of writes
        self.tier.used_size += packet.size
        self.tier.number_of_packets += 1
        self.tier.number_of_write += 1

        with res[0].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, env.now))
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            # update time spent writing
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            res[0].release(req)
            print('%s leaving the resource at %s' % (self.tier.name, env.now))

            self.t1.__str__()
            self.t2.__str__()
            self.forwarder.index.__str__()
            self.forwarder.index.__str__(what="Ghost")
            return
