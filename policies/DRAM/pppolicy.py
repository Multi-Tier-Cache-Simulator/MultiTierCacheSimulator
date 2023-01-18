import math
from collections import OrderedDict
from policies.policy import Policy
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


# time is in nanoseconds
# size is in byte
class Deque(object):
    """Fast searchable queue for default-tier"""

    def __init__(self):
        self.od = OrderedDict()

    def __str__(self):
        for key, value in self.od.items():
            print(value.size.__str__() + ", ", end="")
        print(" ")

    def __len__(self):
        return len(self.od)

    def __contains__(self, k):
        return k in self.od

    def append_left(self, key, value):
        if key in self.od:
            del self.od[key]
        self.od[key] = value

    def pop(self):
        return self.od.popitem(0)[1]

    def remove(self, k):
        del self.od[k]


class PPPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.name = "DRAM_PP"
        self.nb_packets_capacity = 3
        # self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)
        self.p = 0  # Target size for the list T1
        self.t1 = Deque()  # T1: recent cache entries
        self.t2 = Deque()  # T2: frequent entries

    def _replace(self, env: Environment, res, packet: Packet):
        if self.t1 and (
                (self.forwarder.index.packet_in_ghost(packet.name, 'b2') and len(self.t1) == self.p) or (
                len(self.t1) > self.p)):
            old = self.t1.pop()
            print("move from t1 to b1 " + old.name)

            # index update
            self.forwarder.index.del_packet_from_cs(old.name)
            self.forwarder.index.update_packet_ghost(old.name, 'b1')

            # evict data
            self.tier.number_of_eviction_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= old.size
        else:
            old = self.t2.pop()
            print("move from t2 to b2 " + old.name)

            # index update
            self.forwarder.index.del_packet_from_cs(old.name)
            self.forwarder.index.update_packet_ghost(old.name, 'b2')

            # evict data
            self.tier.number_of_eviction_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= old.size

            # store the removed packet from t2 in disk ?
            try:
                target_tier_id = self.forwarder.tiers.index(self.tier) + 1

                # data is important or Disk is free
                if (old.priority == 'h' and len(res[1].queue) < self.forwarder.tiers[
                    target_tier_id].submission_queue_max_size) or len(res[1].queue) < 0.8 * \
                        self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                    print("move data to disk " + old.name)
                    self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')
                # disk is overloaded --> drop packet

                else:
                    print("drop packet" + old.name)
            except:
                print("no other tier")

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s' % (self.tier.name, env.now))
        with res[0].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, env.now))
            # if data already in cache --> return
            if is_write and (self.t1.__contains__(packet.name) or self.t2.__contains__(packet.name)):
                print("data already in dram ")
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                return

            if not is_write and self.t1.__contains__(packet.name):
                # read
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
                self.t1.remove(packet.name)
                self.t2.append_left(packet.name, packet)

                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # increment number of writes
                self.tier.number_of_write += 1

                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                return

            if not is_write and self.t2.__contains__(packet.name):
                # read
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                print(packet.name + " cache hit in t2, move from LRU to MRU of t2")

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
                self.t2.remove(packet.name)
                self.t2.append_left(packet.name, packet)

                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # increment number of writes
                self.tier.number_of_write += 1

                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                return

            if self.forwarder.index.packet_in_ghost(packet.name, 'b1'):
                # write data
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                print(packet.name + " found in b1, move to t2")

                self.p = min(self.nb_packets_capacity, self.p + max(
                    self.forwarder.index.ghost_len('b2') / self.forwarder.index.ghost_len('b1'), 1))

                self._replace(env, res, packet)

                self.t2.append_left(packet.name, packet)

                # index update
                self.forwarder.index.update_packet_tier(packet.name, self.tier)
                self.forwarder.index.del_packet_from_ghost(packet.name)

                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # increment number of writes
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1
                self.tier.used_size += packet.size

                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                return

            if self.forwarder.index.packet_in_ghost(packet.name, 'b2'):
                # time
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                print(packet.name + " found in b2, move to t2")

                self.p = max(0, self.p - max(
                    self.forwarder.index.ghost_len('b1') / self.forwarder.index.ghost_len('b2'), 1))

                self._replace(env, res, packet)

                self.t2.append_left(packet.name, packet)

                # index update
                self.forwarder.index.update_packet_tier(packet.name, self.tier)
                self.forwarder.index.del_packet_from_ghost(packet.name)

                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # increment number of writes
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1
                self.tier.used_size += packet.size

                res[0].release(req)
                print('%s leaving the resource at %s' % (self.tier.name, env.now))
                return

            if len(self.t1) + self.forwarder.index.ghost_len('b1') == self.nb_packets_capacity:
                print(packet.name + " cache miss in all queues")
                # Case A: L1 (T1 u B1) has exactly c pages.
                print(len(self.t1))
                print(self.nb_packets_capacity)
                if len(self.t1) < self.nb_packets_capacity:
                    print("remove LRU page in b1")
                    self.forwarder.index.pop_packet_from_ghost('b1')
                    self._replace(env, res, packet)
                else:
                    old = self.t1.pop()
                    print("Delete LRU page in t1 = " + old.name)

                    # index update
                    self.forwarder.index.del_packet_from_cs(old.name)

                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old.size
            else:
                total = len(self.t1) + self.forwarder.index.ghost_len('b1') + len(
                    self.t2) + self.forwarder.index.ghost_len('b2')
                if total >= self.nb_packets_capacity:
                    if total == (2 * self.nb_packets_capacity):
                        print("Delete LRU page in b2, if |T1| + |T2| + |B1| + |B2| == 2c")
                        self.forwarder.index.pop_packet_from_ghost('b2')
                    self._replace(env, res, packet)

            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            print(packet.name + " write in t1")

            # Finally, fetch x to the cache and move it to MRU position in T1
            self.t1.append_left(packet.name, packet)

            # index update
            self.forwarder.index.update_packet_tier(packet.name, self.tier)

            # update time spent writing
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            # increment number of writes
            self.tier.used_size += packet.size
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1

            res[0].release(req)
            print('%s leaving the resource at %s' % (self.tier.name, env.now))
            return
