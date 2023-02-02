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
        self.name = "LFU"
        # self.nb_packets_capacity = 3
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)
        self.freqToKey = collections.defaultdict(dict)  # frequency to dict of <key, val>
        self.keyToFreq = collections.defaultdict(int)
        self.keyToVal = collections.defaultdict(Packet)

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
        if is_write:
            def first(inp):
                return next(iter(inp))

            # if the packet is not already in cache, prepare its insertion
            if packet.name not in self.keyToVal:
                if len(self.keyToVal) >= self.nb_packets_capacity:
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
                    self.forwarder.index.del_packet_from_cs(old.name)

                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old.size

                    print("%s evict from DISK " % old.name)

            # index update
            self.forwarder.index.update_packet_tier(packet.name, self.tier)

        with res[1].request() as req:
            yield req
            print('%s starting at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))
            if is_write:
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)

                # if packet already exists in cache, increase frequency, else, write it with frequency = 1
                if packet.name in self.keyToVal:
                    curr_freq = self.keyToFreq[packet.name]
                    self.freqToKey[curr_freq].pop(packet.name)
                    self.freqToKey[curr_freq + 1][packet.name] = packet.name
                    self.keyToFreq[packet.name] = curr_freq + 1
                    self.keyToVal[packet.name] = packet

                else:
                    self.freqToKey[1][packet.name] = packet.name
                    self.keyToFreq[packet.name] = 1
                    self.keyToVal[packet.name] = packet

                    # increment number of packets and used size
                    self.tier.used_size += packet.size
                    self.tier.number_of_packets += 1

                # update time spent writing
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                # increment number of writes
                self.tier.number_of_write += 1
            else:
                yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)

                if packet.name in self.keyToVal:
                    curr_freq = self.keyToFreq[packet.name]
                    self.freqToKey[curr_freq].pop(packet.name)
                    self.freqToKey[curr_freq + 1][packet.name] = packet.name
                    self.keyToFreq[packet.name] = curr_freq + 1

                # update time spent reading
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += env.now - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += env.now - packet.timestamp

                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

                # increment number of reads
                self.tier.number_of_reads += 1

            res[1].release(req)
            print('%s leaving the resource at %s for %s %s' % (self.tier.name, env.now, is_write, packet.name))

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from " + self.tier.name.__str__())
        if packet.name in self.keyToVal:
            freq = self.keyToFreq.get(packet.name)
            values = self.freqToKey.get(freq)
            values.pop(packet.name)
            self.keyToFreq.pop(packet.name)
            self.keyToVal.pop(packet.name)

            # index update
            self.forwarder.index.del_packet_from_cs(packet.name)

            # evict data
            self.tier.number_of_prefetching_from_this_tier += 1
            self.tier.used_size -= packet.size
            self.tier.number_of_packets -= 1

