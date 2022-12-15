import math
from decimal import Decimal
from simpy import Environment
from forwarder_structures import Forwarder, Tier, Packet
from policies.policy import Policy


class DRAMLFUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, res, packet: Packet, is_write: bool):
        print('%s arriving at %s' % (self.tier.name, Decimal(env.now)))
        with res[0].request() as req:
            yield req
            print('%s starting at %s' % (self.tier.name, Decimal(env.now)))
            if is_write:
                # free space if capacity full
                def first(inp):
                    return next(iter(inp))

                if packet.name in self.tier.keyToVal:
                    yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                    curr_freq = self.tier.keyToFreq[packet.name]
                    self.tier.freqToKey[curr_freq].pop(packet.name)
                    self.tier.freqToKey[curr_freq + 1][packet.name] = None
                    self.tier.keyToFreq[packet.name] = curr_freq + 1
                    self.tier.keyToVal[packet.name] = packet
                else:
                    if len(self.tier.keyToVal) >= self.nb_packets_capacity:
                        # need to pop out <key,value> with the smallest frequency
                        freq = 1
                        while len(self.tier.freqToKey[freq]) == 0:
                            freq += 1

                        first_key = first(self.tier.freqToKey[freq])
                        self.tier.freqToKey[freq].pop(first_key)
                        del self.tier.keyToFreq[first_key]
                        old = self.tier.keyToVal[first_key]
                        del self.tier.keyToVal[first_key]

                        # index update
                        self.forwarder.index.del_packet_from_cs(old.name)

                        # evict data
                        self.tier.number_of_eviction_from_this_tier += 1
                        self.tier.number_of_packets -= 1
                        self.tier.used_size -= old.size

                        # store the removed packet from dram in disk ?
                        try:
                            target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                            # submission queue is not full
                            if len(res[1].queue) != self.forwarder.tiers[target_tier_id].submission_queue_max_size:
                                print("move data to disk " + old.name)
                                self.forwarder.tiers[target_tier_id].write_packet(env, res, old, cause='eviction')

                            # disk is overloaded --> drop packet
                            else:
                                print("drop packet" + old.name)
                        except:
                            print("no other tier")

                    yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                    self.tier.freqToKey[1][packet.name] = None
                    self.tier.keyToFreq[packet.name] = 1
                    self.tier.keyToVal[packet.name] = packet

                    # index update
                    self.forwarder.index.update_packet_tier(packet.name, self.tier)

                    # time
                    self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                    # write data
                    self.tier.used_size += packet.size
                    self.tier.number_of_packets += 1
                    self.tier.number_of_write += 1

            else:
                yield env.timeout(
                    self.tier.latency + packet.size / self.tier.read_throughput)
                yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
                curr_freq = self.tier.keyToFreq[packet.name]
                self.tier.freqToKey[curr_freq].pop(packet.name)
                self.tier.freqToKey[curr_freq + 1][packet.name] = None
                self.tier.keyToFreq[packet.name] = curr_freq + 1

                # time
                if packet.priority == 'l':
                    self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
                else:
                    self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp

                self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

                # read a data
                self.tier.number_of_reads += 1
            print('%s leaving the resource at %s' % (self.tier.name, Decimal(env.now)))
