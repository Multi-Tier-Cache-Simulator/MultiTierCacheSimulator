import math
from decimal import Decimal
from policies.policy import Policy
from forwarder_structures import Forwarder, Tier, Packet
from simpy.core import Environment


class LFUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, packet: Packet, isWrite: bool):
        print("disk LFU length = " + len(self.tier.cache).__str__())
        # print("index length before = " + len(self.forwarder.index.index).__str__())
        # print("disk LFU = " + self.tier.key_to_freq.items().__str__())
        # print(self.storage.index.__str__())
        if isWrite:
            if self.nb_packets_capacity <= 0:
                print("error cache has no memory")
                return
            if packet.name in self.tier.cache:
                print("data already in cache")
                return
            li = [env.now, 'write', packet]
            self.tier.submission_queue.append(li)
        else:
            li = [env.now, 'read', packet]
            self.tier.submission_queue.append(li)

        lis = self.tier.submission_queue[0]
        if lis[1] == 'read':
            writing = False
        else:
            writing = True

        if writing:
            # key not in key_to_freq and size == capacity --> free space
            if packet.name not in self.tier.cache and self.tier.number_of_packets == self.nb_packets_capacity:
                name, old = list(self.tier.freq_map[self.tier.min_f].items())[0]
                print(old.name + " evicted from " + self.tier.name)
                del self.tier.cache[self.tier.freq_map[self.tier.min_f].popitem(last=False)[0]]
                if not self.tier.freq_map[self.tier.min_f]:
                    del self.tier.freq_map[self.tier.min_f]

                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size

                # index update
                self.forwarder.index.del_packet(old.name)
                # print("index length after = " + len(self.forwarder.index.index).__str__())

            print("writing " + lis[2].name + " to " + self.tier.name.__str__())
            yield env.timeout(lis[2].size / self.tier.write_throughput)
            self.update(packet)

            print('=========')
            print("finished writing " + lis[2].name + " to " + self.tier.name.__str__())
            self.tier.submission_queue.pop(0)

            # index update
            self.forwarder.index.update_packet_tier(packet.name, self.tier)

            # time
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            # write data
            self.tier.used_size += packet.size
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1

            # print("index length after = " + len(self.forwarder.index.index).__str__())
        else:
            print("reading " + lis[2].name + " to " + self.tier.name.__str__())
            yield env.timeout(lis[2].size / self.tier.read_throughput)
            self.update(packet)

            print('=========')
            print("finished reading " + lis[2].name + " to " + self.tier.name.__str__())
            self.tier.submission_queue.pop(0)

            # time
            if packet.priority == 'l':
                self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
            else:
                self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp

            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

            # read a data
            self.tier.number_of_reads += 1

    def update(self, packet: Packet):
        freq = 0
        if packet.name in self.tier.cache:
            freq = self.tier.cache[packet.name]
            del self.tier.freq_map[freq][packet.name]
            if not self.tier.freq_map[freq]:
                del self.tier.freq_map[freq]
                if self.tier.min_f == freq:
                    self.tier.min_f += 1

        freq += 1
        self.tier.min_f = min(self.tier.min_f, freq)
        self.tier.cache[packet.name] = freq
        self.tier.freq_map[freq][packet.name] = packet

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from disk " + self.tier.name.__str__())
        if packet.name in self.tier.cache:
            freq = self.tier.cache[packet.name]
            del self.tier.cache[packet.name]
            del self.tier.freq_map[freq][packet.name]
            if not self.tier.freq_map[freq]:
                del self.tier.freq_map[freq]
            self.tier.number_of_prefetching_from_this_tier += 1
            self.tier.number_of_packets -= 1
            self.tier.used_size -= packet.size
            self.forwarder.index.del_packet(packet.name)
