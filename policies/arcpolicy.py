import math
from decimal import Decimal

from policies.policy import Policy
from forwarder_structures import Forwarder, Tier, Packet
from simpy.core import Environment


# time is in nanoseconds
# size is in byte

class ARCPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def _replace(self, env: Environment, packet: Packet):
        """
               If (T1 is not empty) and ((T1 length exceeds the target p) or (x is in DISK and T1 length == p))
                   Delete the LRU page in T1 (also remove it from the cache), and move it to MRU position in B1.
               else
                   Delete the LRU page in T2 (also remove it from the cache), and move it to MRU position in B2.
               endif
               """
        if self.tier.t1 and (
                (packet.name in self.tier.b2 and len(self.tier.t1) == self.tier.p) or (
                len(self.tier.t1) > self.tier.p)):
            old = self.tier.t1.pop()
            print(self.tier.name + " move from t1 to b1 " + old.name)
            self.tier.b1.appendleft(old.name, old)

            # evict data
            self.tier.number_of_eviction_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= old.size

            # index update
            self.forwarder.index.del_packet(old.name)
        else:
            old = self.tier.t2.pop()
            print(self.tier.name + "move from t2 to b2 " + old.name)
            self.tier.b2.appendleft(old.name, old)

            # evict data
            self.tier.number_of_eviction_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= old.size

            # index update
            self.forwarder.index.del_packet(old.name)

            # store the removed packet from t2 in disk ?
            try:
                target_tier_id = self.forwarder.tiers.index(self.tier) + 1

                # data is important or Disk is free
                if (old.priority == 'h' and self.forwarder.tiers[target_tier_id].submission_queue.__len__() !=
                    self.forwarder.tiers[
                        target_tier_id].submission_queue_max_size) or self.forwarder.tiers[
                    target_tier_id].submission_queue.__len__() < 0.8 * \
                        self.forwarder.tiers[
                            target_tier_id].submission_queue_max_size:
                    print("move data to disk " + old.name)
                    self.forwarder.tiers[target_tier_id].write_packet(env, old, cause='eviction')
                # disk is overloaded --> drop packet
                else:
                    print("drop packet" + old.name)
                    self.tier.b2.appendleft(old.name, old)
            except:
                print("no other tier")

        # print("index length after = " + len(self.forwarder.index.index).__str__())

    def on_packet_access(self, env: Environment, packet: Packet, isWrite: bool):
        print("dram ARC length = " + (len(self.tier.t1) + len(self.tier.t2)).__str__())
        # print("t1 size == " + self.tier.t1.__len__().__str__())
        # print("t2 size == " + self.tier.t2.__len__().__str__())
        # print("b1 size == " + self.tier.b1.__len__().__str__())
        # print("b2 size == " + self.tier.b2.__len__().__str__())
        # print("index length before = " + len(self.forwarder.index.index).__str__())

        # if data already in cache --> return
        if isWrite and (self.tier.t1.__contains__(packet.name) or self.tier.t2.__contains__(packet.name)):
            print("data already in dram ")
            return

        # Case I: x is in T1 or T2. READ FROM T1 OR T2
        #  A cache hit has occurred in ARC(c) and DBL(2c)
        #   Move x to MRU position in T2.
        if not isWrite and self.tier.t1.__contains__(packet.name):
            print("cache hit in t1, move from t1 of t2")
            self.tier.t1.remove(packet.name)
            self.tier.t2.appendleft(packet.name, packet)

            # time
            yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
            if packet.priority == 'l':
                self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
            else:
                self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp

            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
            self.tier.number_of_reads += 1

            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            self.tier.number_of_write += 1
            return

        if not isWrite and self.tier.t2.__contains__(packet.name):
            print("cache hit in t2, move from LRU to MRU of t2")
            self.tier.t2.remove(packet.name)
            self.tier.t2.appendleft(packet.name, packet)

            # time
            # read
            yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
            if packet.priority == 'l':
                self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
            else:
                self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp

            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput
            self.tier.number_of_reads += 1

            # write
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            self.tier.number_of_write += 1
            return

        # Case II: x is in B1 WRITE TO T2
        #  A cache miss has occurred in ARC(c)
        #   ADAPTATION
        #   REPLACE(x)
        #   Move x from B1 to the MRU position in T2 (also fetch x to the cache).

        if self.tier.b1.__contains__(packet.name):
            print("found in b1, move from b1 to t2")
            self.tier.p = min(self.nb_packets_capacity, self.tier.p + max(len(self.tier.b2) / len(self.tier.b1), 1))
            self._replace(env, packet)
            self.tier.b1.remove(packet.name)
            self.tier.t2.appendleft(packet.name, packet)

            # index update
            self.forwarder.index.update_packet_tier(packet.name, self.tier)

            # time
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            # write data
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size
            print("index length after = " + len(self.forwarder.index.index).__str__())
            return

        # Case III: x is in B2 WRITE TO T2
        #  A cache miss has (also) occurred in ARC(c)
        #   ADAPTATION
        #   REPLACE(x, p)
        #   Move x from B2 to the MRU position in T2 (also fetch x to the cache).

        if self.tier.b2.__contains__(packet.name):
            print("found in b2, move from b2 to t2")
            self.tier.p = max(0, self.tier.p - max(len(self.tier.b1) / len(self.tier.b2), 1))
            self._replace(env, packet)

            self.tier.b2.remove(packet.name)
            self.tier.t2.appendleft(packet.name, packet)

            # index update
            self.forwarder.index.update_packet_tier(packet.name, self.tier)

            # time
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            # write data
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            self.tier.used_size += packet.size
            print("index length after = " + len(self.forwarder.index.index).__str__())
            return

        # Case IV: x is not in (T1 u B1 u T2 u B2) WRITE IN T1
        #  A cache miss has occurred in ARC(c) and DBL(2c)
        if len(self.tier.t1) + len(self.tier.b1) == self.nb_packets_capacity:
            print("cache miss in all queues")
            # Case A: L1 (T1 u B1) has exactly c pages.
            if len(self.tier.t1) < self.nb_packets_capacity:
                print("remove LRU page in b1")
                self.tier.b1.pop()
                self._replace(env, packet)
            else:
                # Here B1 is empty.
                # Delete LRU page in T1 (cache)
                # evict data
                old = self.tier.t1.pop()
                print("Delete LRU page in t1 = " + old.name)

                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size

                # index update
                self.forwarder.index.del_packet(old.name)
                print("index length after = " + len(self.forwarder.index.index).__str__())
        else:
            # Case B: L1 (T1 u B1) has less than c pages.
            total = len(self.tier.t1) + len(self.tier.b1) + len(self.tier.t2) + len(self.tier.b2)
            if total >= self.nb_packets_capacity:
                # Delete LRU page in B2, if |T1| + |T2| + |B1| + |B2| == 2c
                if total == (2 * self.nb_packets_capacity):
                    print("Delete LRU page in b2, if |T1| + |T2| + |B1| + |B2| == 2c")
                    self.tier.b2.pop()

                # REPLACE(x, p)
                self._replace(env, packet)
        print('write in t1')

        # Finally, fetch x to the cache and move it to MRU position in T1
        self.tier.t1.appendleft(packet.name, packet)

        # index update
        self.forwarder.index.update_packet_tier(packet.name, self.tier)

        # time
        yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
        self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

        # write data
        self.tier.number_of_packets += 1
        self.tier.number_of_write += 1
        self.tier.used_size += packet.size
        print("index length after = " + len(self.forwarder.index.index).__str__())
        return
