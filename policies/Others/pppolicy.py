import math
from common.deque import Deque
from common.penalty import penalty_by_priority
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder_structures.forwarder import Forwarder
from simpy.core import Environment


# time is in nanoseconds
# size is in byte


class PPPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.name = "PP"
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)
        print(self.nb_packets_capacity)
        self.p = 0  # Target size for the list T1
        self.t1 = Deque()  # T1: recent cache entries
        self.t2 = Deque()  # T2: frequent cache entries

    def _replace(self, env: Environment, res, packet: Packet):
        in_b2 = yield env.process(self.forwarder.index.packet_in_ghost(packet.name, 'b2'))
        if self.t1 and ((len(self.t1) > self.p) or (in_b2 and len(self.t1) == self.p)):
            name, old = self.t1.get_without_pop()
            self.t1.pop()
            print("evict from t1 to b1 " + old.name)
            # index update
            yield env.process(self.forwarder.index.update_packet_ghost(old.name, 'b1'))
            yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
            # evict data
            self.tier.number_of_eviction_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= old.size
        else:
            name, old = self.t2.get_without_pop()
            if old.priority == "l" or (old.priority == "h" and penalty_by_priority()):
                self.t2.pop()
                print("evict from t2 to b2 " + old.name)
                # index update
                yield env.process(self.forwarder.index.update_packet_ghost(old.name, 'b2'))
                yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size
                # store the removed packet from t2 in disk ?
                # TODO change to evict every data to disk
                try:
                    target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                    # Disk is free
                    if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                        print("evict from t2 to disk " + old.name)
                        self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')
                    # disk is overloaded --> drop packet
                    else:
                        print("drop packet" + old.name)
                except Exception as e:
                    print(e.__str__())
                    print("no other tier")
            else:
                deleted = False
                for name, old in self.t2.items():
                    if old.priority == "l":
                        deleted = True
                        self.t2.remove(name)
                        print("evict from t2 to b2 " + old.name)
                        # index update
                        yield env.process(self.forwarder.index.update_packet_ghost(old.name, 'b2'))
                        yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
                        # evict data
                        self.tier.number_of_eviction_from_this_tier += 1
                        self.tier.number_of_packets -= 1
                        self.tier.used_size -= old.size
                        # store the removed packet from t2 in disk ?
                        # TODO change to evict every data to disk
                        try:
                            target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                            # Disk is free
                            if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                                print("evict from t2 to disk " + old.name)
                                self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')
                            # disk is overloaded --> drop packet
                            else:
                                print("drop packet" + old.name)
                        except Exception as e:
                            print(e.__str__())
                            print("no other tier")
                        break
                if not deleted:
                    name, old = self.t2.get_without_pop()
                    self.t2.pop()
                    print("evict from t2 to b2 " + old.name)
                    # index update
                    yield env.process(self.forwarder.index.update_packet_ghost(old.name, 'b2'))
                    yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old.size
                    # store the removed packet from t2 in disk ?
                    # TODO change to evict every data to disk
                    try:
                        target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                        # Disk is free
                        if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                            print("evict from t2 to disk " + old.name)
                            self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')
                        # disk is overloaded --> drop packet
                        else:
                            print("drop packet" + old.name)
                    except Exception as e:
                        print(e.__str__())
                        print("no other tier")

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool, cause=None):
        # print("size = ", res[0].count.__str__())
        print('%s arriving at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
        self.t1.__str__()
        self.t2.__str__()
        if not is_write and self.t1.__contains__(packet.name):
            print(packet.name + " hit in t1, promote to MRU t2")
            self.t1.remove(packet.name)
            self.t2.append_left(packet.name, packet)
            with res[0].request() as req:
                yield req
                print('%s starting at %s' % (self.tier.name, env.now))
                # read
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
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
                return

        if not is_write and self.t2.__contains__(packet.name):
            print(packet.name + " hit in t2, promote to MRU t2")
            self.t2.remove(packet.name)
            self.t2.append_left(packet.name, packet)
            with res[0].request() as req:
                yield req
                print('%s starting at %s' % (self.tier.name, env.now))
                # read
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
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
                return

        in_b1 = yield env.process(self.forwarder.index.packet_in_ghost(packet.name, 'b1'))
        if in_b1:
            print(packet.name + " hit in b1, promote to MRU t2")
            len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
            len_b2 = yield env.process(self.forwarder.index.ghost_len('b2'))
            self.p = min(self.nb_packets_capacity, self.p + max(len_b2 / len_b1, 1))
            yield env.process(self._replace(env, res, packet))
            # index update
            yield env.process(self.forwarder.index.del_packet_from_ghost(packet.name))
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
            # increment number of writes
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size
            self.t2.append_left(packet.name, packet)
            with res[0].request() as req:
                yield req
                print('%s starting at %s' % (self.tier.name, env.now))
                # write data
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                return

        in_b2 = yield env.process(self.forwarder.index.packet_in_ghost(packet.name, 'b2'))
        if in_b2:
            print(packet.name + " hit in b2, promote to MRU t2")
            len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
            len_b2 = yield env.process(self.forwarder.index.ghost_len('b2'))
            self.p = max(0, self.p - max(len_b1 / len_b2, 1))
            yield env.process(self._replace(env, res, packet))
            # index update
            yield env.process(self.forwarder.index.del_packet_from_ghost(packet.name))
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
            # increment number of writes
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size
            self.t2.append_left(packet.name, packet)
            with res[0].request() as req:
                yield req
                print('%s starting at %s' % (self.tier.name, env.now))
                # time
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                return

        len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
        if len(self.t1) + len_b1 == self.nb_packets_capacity:
            print(packet.name + " cache miss in all queues")
            # Case A: L1 (T1 u B1) has exactly c pages.
            if len(self.t1) < self.nb_packets_capacity:
                print("evict from b1")
                yield env.process(self.forwarder.index.pop_packet_from_ghost('b1'))
                yield env.process(self._replace(env, res, packet))
            else:
                name, old = self.t1.get_without_pop()
                self.t1.pop()
                self.tier.evicted_from_t1 += 1
                print("evict from t1 = " + old.name)
                yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size
        else:
            len_b1 = yield env.process(self.forwarder.index.ghost_len('b1'))
            len_b2 = yield env.process(self.forwarder.index.ghost_len('b2'))
            total = len(self.t1) + len_b1 + len(self.t2) + len_b2
            if total >= self.nb_packets_capacity > len(self.t1) + len_b1:
                if total == (2 * self.nb_packets_capacity):
                    print("evict from b2")
                    yield env.process(self.forwarder.index.pop_packet_from_ghost('b2'))
                yield env.process(self._replace(env, res, packet))

        # TODO try this code
        # data coming from disk
        if cause == "prefetching":
            print(packet.name + " hit in disk, promote to MRU t2")
            self.t2.append_left(packet.name, packet)
            # increment number of writes
            self.tier.used_size += packet.size
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            # index update
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
            return

        if packet.priority == "h":
            print(packet.name + " high priority packet, insert in t2")
            self.t2.append_left(packet.name, packet)
        # elif self.t1.__len__() >= self.nb_packets_capacity * 0.3:
        #     name, old = self.t1.get_without_pop()
        #     self.t1.pop()
        #     # index update
        #     yield env.process(self.forwarder.index.del_packet_from_cs(old.name))
        #     # evict data
        #     self.tier.number_of_eviction_from_this_tier += 1
        #     self.tier.number_of_packets -= 1
        #     self.tier.used_size -= old.size
        #     print(packet.name + " low priority packet, insert in t1")
        #     self.t1.append_left(packet.name, packet)
        else:
            print(packet.name + " low priority packet, insert in t1")
            self.t1.append_left(packet.name, packet)
        # increment number of writes
        self.tier.used_size += packet.size
        self.tier.number_of_packets += 1
        self.tier.number_of_write += 1
        # index update
        yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))
        with res[0].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, env.now))
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            # update time spent writing
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            res[0].release(req)
            print('%s leaving the resource at %s' % (self.tier.name, env.now))
            return
