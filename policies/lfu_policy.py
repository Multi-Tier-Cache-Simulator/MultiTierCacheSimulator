import collections
import math
from simpy import Environment
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from policies.policy import Policy


class LFUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)

        self.c = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

        self.freqToKey = collections.defaultdict(dict)  # frequency to dict of <key, val>
        self.keyToFreq = collections.defaultdict(int)
        self.keyToVal = collections.defaultdict(Packet)

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
        if self.c == 0:
            print("cache units == %s" % self.c)
            return

        if is_write:
            def first(inp):
                return next(iter(inp))

            if len(self.keyToVal) >= self.c:
                # need to pop out <key,value> with the smallest frequency
                freq = 1
                while len(self.freqToKey[freq]) == 0:
                    freq += 1
                first_key = first(self.freqToKey[freq])
                self.freqToKey[freq].pop(first_key)
                del self.keyToFreq[first_key]
                old = self.keyToVal[first_key]
                del self.keyToVal[first_key]
                # index update
                yield env.process(self.forwarder.index.del_packet_from_cs(old.name))

                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size

                print("evict %s from %s " % (old.name, self.tier.name))
                try:
                    target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                    # submission queue is not full
                    if len(res[target_tier_id].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                        print("evict to disk %s" % old.name)
                        yield env.process(
                            self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction'))
                    # disk is overloaded --> drop packet
                    else:
                        print("drop packet %s" % old.name)
                except Exception as e:
                    print("error : %s" % e)

            self.freqToKey[1][packet.name] = packet.name
            self.keyToFreq[packet.name] = 1
            self.keyToVal[packet.name] = packet

            # index update
            yield env.process(self.forwarder.index.update_packet_tier(packet.name, self.tier))

            # increment number of packets and used size
            self.tier.used_size += packet.size
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1

        elif packet.name in self.keyToVal:
            curr_freq = self.keyToFreq[packet.name]
            self.freqToKey[curr_freq].pop(packet.name)
            self.freqToKey[curr_freq + 1][packet.name] = packet.name
            self.keyToFreq[packet.name] = curr_freq + 1

            # increment number of reads
            self.tier.number_of_reads += 1

        with res[self.forwarder.tiers.index(self.tier)].request() as req:
            yield req
            print('%s starting at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
            if is_write:
                # writing
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput
            elif packet.name in self.keyToVal:
                # reading
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp
                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

            res[self.forwarder.tiers.index(self.tier)].release(req)
            print(self.keyToVal.keys().__str__())
            self.forwarder.index.__str__()
            self.forwarder.index.__str__(what="Ghost")
            print('%s leaving the resource at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))

    def prefetch_packet(self, env: Environment, packet: Packet):
        print("prefetch packet from %s" % self.tier.name)
        if packet.name in self.keyToVal:
            freq = self.keyToFreq.get(packet.name)
            values = self.freqToKey.get(freq)
            values.pop(packet.name)
            self.keyToFreq.pop(packet.name)
            self.keyToVal.pop(packet.name)

            # index update
            yield env.process(self.forwarder.index.del_packet_from_cs(packet.name))

            # evict data
            self.tier.number_of_prefetching_from_this_tier += 1
            self.tier.used_size -= packet.size
            self.tier.number_of_packets -= 1
