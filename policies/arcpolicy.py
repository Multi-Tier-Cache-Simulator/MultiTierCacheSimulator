import numpy
from policies.policy import Policy
from storage_structures import StorageManager, Tier
from simpy.core import Environment


class ARCPolicy(Policy):
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        Policy.__init__(self, tier, storage, env)

    def replace(self, timestamp: int, name: str, size: int, priority: str):
        """
               If (T1 is not empty) and ((T1 length exceeds the target p) or (x is in DISK and T1 length == p))
                   Delete the LRU page in T1 (also remove it from the cache), and move it to MRU position in B1.
               else
                   Delete the LRU page in T2 (also remove it from the cache), and move it to MRU position in B2.
               endif
               """
        p1 = 0.5
        p2 = 0.7
        if self.tier.t1 and (
                (name in self.tier.b2 and len(self.tier.t1) == self.tier.p) or (len(self.tier.t1) > self.tier.p)):
            print("delete from t1")
            old = self.tier.t1.pop()
            self.tier.b1.appendleft(old)
            self.tier.used_size -= size
            self.tier.number_of_packets = -1
        else:
            old = self.tier.t2.pop()
            self.tier.used_size -= size
            self.tier.number_of_packets = -1
            x = numpy.random.uniform(low=0.0, high=1.0, size=None)
            print(x)
            if x < p1:
                # drop current packet
                print("drop current packet")
                self.tier.b2.appendleft(old)
            if p1 < x < p2:
                # drop HPC
                target_tier_id = self.storage.tiers.index(self.tier) + 1
                print("migrate to disk")
                self.storage.migrate(timestamp, old, size, priority, self.storage.tiers[target_tier_id])
                self.storage.tiers[target_tier_id].used_size += size
                self.storage.tiers[target_tier_id].number_of_packets = +1
            if x > p2:
                # drop LPC
                target_tier_id = self.storage.tiers.index(self.tier) + 1
                self.storage.migrate(timestamp, old, size, priority, self.storage.tiers[target_tier_id])
                self.storage.tiers[target_tier_id].used_size += size
                self.storage.tiers[target_tier_id].number_of_packets = +1

    def on_packet_access(self, timestamp: int, name: str, size: int, priority: str, isWrite: bool):
        # Case I: x is in T1 or T2. READ FROM T1 OR T2
        #  A cache hit has occurred in ARC(c) and DBL(2c)
        #   Move x to MRU position in T2.
        print("==========================")
        print("t1 = " + self.tier.t1.__str__() + " size == " + self.tier.t1.__len__().__str__())
        print("t2 = " + self.tier.t2.__str__() + " size == " + self.tier.t2.__len__().__str__())
        print("b1 = " + self.tier.b1.__str__() + " size == " + self.tier.b1.__len__().__str__())
        print("b2 = " + self.tier.b2.__str__() + " size == " + self.tier.b2.__len__().__str__())
        if self.tier.t1.__contains__(name):
            print("cache hit in t1")
            self.tier.t1.remove(name)
            self.tier.t2.appendleft(name)
            self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
            self.tier.time_spent_reading += self.tier.latency + size / self.tier.throughput
            print("data moved from t1 of t2")
            return

        if self.tier.t2.__contains__(name):
            print("cache hit in t2")
            self.tier.t2.remove(name)
            self.tier.t2.appendleft(name)
            self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
            self.tier.time_spent_reading += self.tier.latency + size / self.tier.throughput
            print("data moved from LRU to MRU of t2")
            return

        # Case II: x is in B1 WRITE TO T2
        #  A cache miss has occurred in ARC(c)
        #   ADAPTATION
        #   REPLACE(x)
        #   Move x from B1 to the MRU position in T2 (also fetch x to the cache).

        if self.tier.b1.__contains__(name):
            print("data found in b1")
            self.tier.p = min(71, self.tier.p + max(len(self.tier.b2) / len(self.tier.b1), 1))
            print("p = " + self.tier.p.__str__())
            self.replace(timestamp, name, size, priority)
            self.tier.b1.remove(name)
            self.tier.t2.appendleft(name)
            self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
            self.storage.index.update_packet_tier(name, self.tier)
            self.tier.number_of_packets = +1
            self.tier.used_size += size
            print("data moved from b1 to t2")
            return

        # Case III: x is in B2 WRITE TO T2
        #  A cache miss has (also) occurred in ARC(c)
        #   ADAPTATION
        #   REPLACE(x, p)
        #   Move x from B2 to the MRU position in T2 (also fetch x to the cache).

        if self.tier.b2.__contains__(name):
            print("data found in b2")
            self.tier.p = max(0, self.tier.p - max(len(self.tier.b1) / len(self.tier.b2), 1))
            print("p = " + self.tier.p.__str__())
            self.replace(timestamp, name, size, priority)
            self.tier.b2.remove(name)
            self.tier.t2.appendleft(name)
            print("data moved from b2 to t2")
            self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
            self.storage.index.update_packet_tier(name, self.tier)
            self.tier.number_of_packets = +1
            self.tier.used_size += size
            return

        # Case IV: x is not in (T1 u B1 u T2 u B2) WRITE IN T1
        #  A cache miss has occurred in ARC(c) and DBL(2c)
        print("Cache miss")
        if len(self.tier.t1) + len(self.tier.b1) == 71:
            print("Case A: L1 (T1 u B1) has exactly c pages.")
            # Case A: L1 (T1 u B1) has exactly c pages.
            if len(self.tier.t1) < 71:
                print("Delete LRU page in B1. REPLACE(x, p)")
                # Delete LRU page in B1. REPLACE(x, p)
                self.tier.b1.pop()
                self.replace(timestamp, name, size, priority)
            else:
                print("Here B1 is empty. Delete LRU page in T1 (cache)")
                # Here B1 is empty.
                # Delete LRU page in T1 (cache)
                self.storage.index.del_packet(self.tier.t1.pop())
                self.tier.number_of_packets = -1
                self.tier.used_size -= size
        else:
            # Case B: L1 (T1 u B1) has less than c pages.
            print("Case B: L1 (T1 u B1) has less than c pages")
            total = len(self.tier.t1) + len(self.tier.b1) + len(self.tier.t2) + len(self.tier.b2)
            print("total" + total.__str__())
            if total >= 71:
                # Delete LRU page in B2, if |T1| + |T2| + |B1| + |B2| == 2c
                print("total >= 71")
                if total == (2 * 71):
                    print("Delete LRU page in B2, if |T1| + |T2| + |B1| + |B2| == 2c")
                    self.tier.b2.pop()

                # REPLACE(x, p)
                self.replace(timestamp, name, size, priority)

        # Finally, fetch x to the cache and move it to MRU position in T1
        self.tier.t1.appendleft(name)
        self.tier.time_spent_writing += self.tier.latency + size / self.tier.throughput
        self.storage.index.update_packet_tier(name, self.tier)
        self.tier.number_of_packets = +1
        self.tier.used_size += size

        if self.storage.index.tier_has_packet(self.tier, name):
            print("data written in t1")
        return

# def on_tier_nearly_full(self):
#    print("on_tier_nearly_full")
#   target_tier_id = self.storage.tiers.index(self.tier) + 1  # iterating to the next tier
#  if target_tier_id < len(self.storage.tiers):  # checking this next tier do exist
#     while self.tier.used_size > self.tier.max_size * (self.tier.target_occupation - 0.15):
#        self.storage.migrate(name, size,
#                            self.storage.tiers[target_tier_id], timestamp)  # migrating
# if self.tier.used_size > self.tier.max_size * (self.tier.target_occupation - 0.15):
#   print("migrate")
# target_tier_id = self.storage.tiers.index(self.tier) + 1
# self.storage.migrate(name, size, self.storage.tiers[target_tier_id], timestamp)
# self.storage.index.update_packet_tier(name, self.storage.tiers[target_tier_id])
# self.storage.tiers[target_tier_id].number_of_packets = +1
# self.storage.tiers[target_tier_id].used_size += size
# else:
# else:
#   print(f'Tier {self.tier.name} is nearly full, but there is no other tier to discharge load.')
