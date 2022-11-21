import math
import random
from decimal import Decimal
from policies.policy import Policy
from forwarder_structures import Forwarder, Tier, Packet
from simpy.core import Environment


class RandPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, packet: Packet, isWrite: bool):
        print("disk random length = " + len(self.tier.random_struct).__str__())
        # print("index length before = " + len(self.forwarder.index.index).__str__())
        # print("disk random = " + self.tier.random_struct.__str__())
        # print(self.storage.index.__str__())
        if isWrite:
            if packet.name in self.tier.random_struct:
                print("data already in cache " + packet.name)
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
            if len(self.tier.random_struct) >= self.nb_packets_capacity:
                print("random.randrange(len(self.tier.random_struct) = " + random.randrange(
                    len(self.tier.random_struct)).__str__())
                print(self.forwarder.index.__str__())
                old = self.tier.random_struct.pop(
                    list(self.tier.random_struct.keys())[random.randrange(len(self.tier.random_struct))])
                print(old.name + " evicted from " + self.tier.name)

                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size

                # index update
                self.forwarder.index.del_packet(old.name)
                # print("index length after = " + len(self.forwarder.index.index).__str__())

            print("writing " + lis[2].name + " to " + self.tier.name.__str__())
            yield env.timeout(lis[2].size / self.tier.write_throughput)
            self.tier.random_struct[packet.name] = packet

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
        else:
            print("reading " + lis[2].name + " to " + self.tier.name.__str__())
            yield env.timeout(lis[2].size / self.tier.read_throughput)

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

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from disk " + self.tier.name.__str__())
        del self.tier.random_struct[packet.name]
        self.tier.number_of_prefetching_from_this_tier += 1
        self.tier.number_of_packets -= 1
        self.tier.used_size -= packet.size
        self.forwarder.index.del_packet(packet.name)
