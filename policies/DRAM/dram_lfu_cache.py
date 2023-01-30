import collections
import math
from simpy import Environment
from common.packet import Packet
from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from policies.policy import Policy


class DRAMLFUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.name = "DRAM_LFU"
        # self.nb_packets_capacity = 3
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)
        self.freqToKey = collections.defaultdict(dict)  # frequency to dict of <key, val>
        self.keyToFreq = collections.defaultdict(int)
        self.keyToVal = collections.defaultdict(Packet)

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print(res[0].queue)
        print('%s arriving at %s' % (self.tier.name, env.now))
        with res[0].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, env.now))
            if is_write:
                def first(inp):
                    return next(iter(inp))

                # check if packet already exists in cache
                if packet.name in self.keyToVal:
                    yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)

                    curr_freq = self.keyToFreq[packet.name]
                    self.freqToKey[curr_freq].pop(packet.name)
                    self.freqToKey[curr_freq + 1][packet.name] = packet.name
                    self.keyToFreq[packet.name] = curr_freq + 1
                    self.keyToVal[packet.name] = packet

                    # update time spent writing
                    self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                    # increment number of writes
                    self.tier.number_of_write += 1
                else:
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

                        try:
                            target_tier_id = self.forwarder.tiers.index(self.tier) + 1

                            # submission queue is not full
                            if len(res[1].queue) < self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                                print("move data to disk " + old.name)
                                self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')

                            # disk is overloaded --> drop packet
                            else:
                                print("drop packet" + old.name)
                        except:
                            print("no other tier")

                    yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)

                    self.freqToKey[1][packet.name] = packet.name
                    self.keyToFreq[packet.name] = 1
                    self.keyToVal[packet.name] = packet

                    # index update
                    self.forwarder.index.update_packet_tier(packet.name, self.tier)

                    # update time spent writing
                    self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                    # increment number of packets and used size
                    self.tier.used_size += packet.size
                    self.tier.number_of_packets += 1
                    self.tier.number_of_write += 1
            else:
                if packet.name in self.keyToVal:
                    yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)

                    curr_freq = self.keyToFreq[packet.name]
                    self.freqToKey[curr_freq].pop(packet.name)
                    self.freqToKey[curr_freq + 1][packet.name] = packet.name
                    self.keyToFreq[packet.name] = curr_freq + 1

                    # update time spent reading
                    if packet.priority == 'l':
                        self.tier.low_p_data_retrieval_time += (env.now) - packet.timestamp
                    else:
                        self.tier.high_p_data_retrieval_time += (env.now) - packet.timestamp

                    self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

                    # increment number of reads
                    self.tier.number_of_reads += 1
                else:
                    raise ValueError(f"Key {packet.name} not found in cache.")

            res[0].release(req)
            print(self.keyToVal.__str__())
            print('%s leaving the resource at %s' % (self.tier.name, (env.now)))
