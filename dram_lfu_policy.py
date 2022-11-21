import math
from decimal import Decimal
from policies.policy import Policy
from forwarder_structures import Forwarder, Tier, Packet
from simpy.core import Environment


class DRAMLFUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, packet: Packet, isWrite: bool):
        print("dram LFU length = " + len(self.tier.cache).__str__())
        # print("index length before = " + len(self.forwarder.index.index).__str__())
        # print("dram LFU = " + self.tier.key_to_freq.items().__str__())
        # print(self.storage.index.__str__())
        print("self.nb_capa = " + self.nb_packets_capacity.__str__())
        if isWrite:
            if packet.name in self.tier.cache:
                self.update(packet)
            else:
                self.tier.cache[packet.name] = (packet, 1)
                self.tier.freq_map[1][packet.name] = (packet, 1)
                # time
                yield env.timeout(
                    self.tier.latency + packet.size / self.tier.write_throughput)
                self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

                self.update(packet)

                # index update
                self.forwarder.index.update_packet_tier(packet.name, self.tier)

                # write data
                self.tier.used_size += packet.size
                self.tier.number_of_packets += 1
                self.tier.number_of_write += 1

                if self.nb_packets_capacity == 0:
                    old = self.tier.freq_map[self.tier.min_f].popitem(last=False)
                    self.tier.cache.pop(old[0])
                    self.nb_packets_capacity += 1

                    # evict data
                    self.tier.number_of_eviction_from_this_tier += 1
                    self.tier.number_of_packets -= 1
                    self.tier.used_size -= old[1][0].size

                    # index update
                    self.forwarder.index.del_packet(old[0])

                    # print("index length after = " + len(self.forwarder.index.index).__str__())
                    # store the removed packet from dram in disk ?
                    try:
                        target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                        # submission queue is not full
                        if self.forwarder.tiers[target_tier_id].submission_queue.__len__() != self.forwarder.tiers[
                                target_tier_id].submission_queue_max_size:
                            print("move data to disk " + old[0])
                            self.forwarder.tiers[target_tier_id].write_packet(env, old[1][0], cause='eviction')
                        # disk is overloaded --> drop packet
                        else:
                            print("drop packet" + old[0])
                    except:
                        print("no other tier")
                else:
                    self.nb_packets_capacity -= 1
                    self.tier.min_f = 1

            # print("index length after = " + len(self.forwarder.index.index).__str__())
        else:
            yield env.timeout(self.tier.latency + packet.size / self.tier.read_throughput)
            self.update(packet)

            # time
            if packet.priority == 'l':
                self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
            else:
                self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp

            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

            # read a data
            self.tier.number_of_reads += 1

    def update(self, packet: Packet):
        _, freq = self.tier.cache[packet.name]
        self.tier.freq_map[freq].pop(packet.name)
        if len(self.tier.freq_map[self.tier.min_f]) == 0:
            self.tier.min_f += 1
        self.tier.freq_map[freq + 1][packet.name] = (packet, freq + 1)
        self.tier.cache[packet.name] = (packet, freq + 1)
