import math
from decimal import Decimal
from policies.policy import Policy
from forwarder_structures import Forwarder, Tier, Packet
from simpy import Environment


class LFUPolicy(Policy):
    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        Policy.__init__(self, env, forwarder, tier)
        self.nb_packets_capacity = math.trunc(self.tier.max_size * self.tier.target_occupation / forwarder.slot_size)

    def on_packet_access(self, env: Environment, packet: Packet, isWrite: bool):
        print("disk LFU length = " + len(self.tier.cache).__str__())
        # print("index length before = " + len(self.forwarder.index.index).__str__())
        # print("dram LFU = " + self.tier.key_to_freq.items().__str__())
        # print(self.storage.index.__str__())
        print("self.nb_capa = " + self.nb_packets_capacity.__str__())
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
            print("writing " + lis[2].name + " to " + self.tier.name.__str__())
            yield env.timeout(self.tier.latency + packet.size / self.tier.write_throughput)
            self.put(env, packet.name, packet)
            print('=========')
            print("finished writing " + lis[2].name + " to " + self.tier.name.__str__())
            self.tier.submission_queue.pop(0)
        else:
            print("reading " + lis[2].name + " to " + self.tier.name.__str__())
            yield env.timeout(
                self.tier.latency + packet.size / self.tier.read_throughput)
            self.get(env, packet.name, packet)
            print('=========')
            print("finished reading " + lis[2].name + " to " + self.tier.name.__str__())
            self.tier.submission_queue.pop(0)

    def get(self, env, key, packet):
        """
        :type key: int
        :rtype: int
        """
        if key in self.tier.cache:
            # time
            if packet.priority == 'l':
                self.tier.low_p_data_retrieval_time += Decimal(env.now) - packet.timestamp
            else:
                self.tier.high_p_data_retrieval_time += Decimal(env.now) - packet.timestamp

            self.tier.time_spent_reading += self.tier.latency + packet.size / self.tier.read_throughput

            # read a data
            self.tier.number_of_reads += 1

            # Update new frequency
            # Update freq_map
            # Move key to front in its linkedHashSet
            # Update new minimum frequency
            v, f = self.tier.cache[key][0], self.tier.cache[key][1]
            self.tier.cache[key][1] += 1

            f_count_zero = False
            self.tier.freq_map[f].remove(key)
            if self.tier.freq_map[f].size() == 0:
                f_count_zero = True
                self.tier.freq_map.pop(f)
            self.tier.freq_map[f + 1].appendleft(key, v)

            if f == self.tier.min_f and f_count_zero == True:
                self.tier.min_f += 1

        return -1

    def put(self, env, key, packet: Packet):
        """
        :type key: int
        :type packet: int
        :rtype: void
        """
        if self.nb_packets_capacity == 0:
            print("error cache has no memory")
            return
        if key in self.tier.cache:
            print("data already in cache")
            self.tier.cache[key][0] = packet
            self.get(env, key, packet)
        else:
            curr_size = len(self.tier.cache)
            if curr_size == self.nb_packets_capacity:
                min_list = self.tier.freq_map[self.tier.min_f]
                y = min_list.pop()
                x = self.tier.cache.pop(y)
                old = x[0]
                # evict data
                self.tier.number_of_eviction_from_this_tier += 1
                self.tier.number_of_packets -= 1
                self.tier.used_size -= old.size

                # index update
                self.forwarder.index.del_packet(old.name)

                # store the removed packet from dram in disk ?
                try:
                    target_tier_id = self.forwarder.tiers.index(self.tier) + 1
                    # submission queue is not full
                    if self.forwarder.tiers[target_tier_id].submission_queue.__len__() != self.forwarder.tiers[
                        target_tier_id].submission_queue_max_size:
                        print("move data to disk " + old.name)
                        self.forwarder.tiers[target_tier_id].write_packet(env, old, cause='eviction')
                    # disk is overloaded --> drop packet
                    else:
                        print("drop packet" + old.name)
                except:
                    print("no other tier")

            self.tier.cache[key] = [packet, 1]
            self.tier.freq_map[1].appendleft(key, packet)
            self.tier.min_f = 1

            # time
            self.tier.time_spent_writing += self.tier.latency + packet.size / self.tier.write_throughput

            # index update
            self.forwarder.index.update_packet_tier(packet.name, self.tier)

            # write data
            self.tier.used_size += packet.size
            self.tier.number_of_packets += 1
            self.tier.number_of_write += 1
            return

    def prefetch_packet(self, packet: Packet):
        print("prefetch packet from disk " + self.tier.name.__str__())
        f = self.tier.cache[packet.name][1]
        self.tier.cache.pop(packet.name)
        self.tier.freq_map[f].remove(packet.name)

        self.tier.number_of_prefetching_from_this_tier += 1
        self.tier.number_of_packets -= 1
        self.tier.used_size -= packet.size
        self.forwarder.index.del_packet(packet.name)

