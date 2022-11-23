import csv
from decimal import Decimal
from resources import NDN_PACKETS
from forwarder_structures import Packet
from traces.trace import Trace


class NDNTrace(Trace):
    _COLUMN_NAMES = ("packetType", "timestamp", "name", "size", "priority", "InterestLifetime", "responseTime")

    def __init__(self):
        Trace.__init__(self)
        self.data = []

    def gen_data(self, trace_len_limit=-1):
        for path in NDN_PACKETS:
            with open(path, encoding='utf8') as read_obj:
                csv_reader = csv.reader(read_obj, delimiter=',')
                self.data = list(csv_reader)
                if trace_len_limit > 0:
                    self.data = self.data[:min(len(self.data), trace_len_limit)]

    def read_data_line(self, env, res, forwarder, line, log_file, logs_enabled=True):
        """Read a line, and fire events if necessary"""
        print("=========")
        data_back, timestamp, name, size, priority, interest_life_time, response_time = line
        timestamp = int(timestamp)
        size = int(size)
        interest_life_time = int(interest_life_time)
        response_time = int(response_time)
        packet = Packet(data_back, timestamp, name, size, priority)
        # if priority == 'h':
        #     return
        # delete expired pit entries
        forwarder.pit.update_pit_times(env)

        # cache hit
        if forwarder.index.index_has_name(name):
            print("cache hit")
            print('interest on ' + packet.name + ' arrives at ' + env.now.__str__())
            print("read packet = " + name)
            tier = forwarder.index.get_packet_tier(name)
            # if data not in default tier
            if tier.name.__str__() != forwarder.get_default_tier().name.__str__():
                # prefetch data to default-tier
                # chr
                tier.chr += 1
                if priority == 'h':
                    tier.chrhpc += 1
                else:
                    if priority == 'l':
                        tier.chrlpc += 1

                print("Prefetch data to default tier " + forwarder.get_default_tier().name.__str__())
                tier.prefetch_packet(packet)
                forwarder.get_default_tier().write_packet(env, res, packet, cause="prefetching")

                # read data from dram
                print("read from dram")
                forwarder.get_default_tier().read_packet(env, res, packet)
                print("finished reading from dram in ndn_trace")
            else:
                # read data from dram
                print("read from dram")
                forwarder.get_default_tier().read_packet(env, res, packet)
                # chr
                forwarder.get_default_tier().chr += 1
                if priority == 'h':
                    forwarder.get_default_tier().chrhpc += 1
                else:
                    if priority == 'l':
                        forwarder.get_default_tier().chrlpc += 1
            return

        # cache miss and pit hit
        if forwarder.pit.pit_has_name(name):
            print("cache miss, pit hit")
            forwarder.pit.add_to_pit(name, env.now + interest_life_time)
            forwarder.nAggregation += 1
            return

        # cache miss and pit miss
        print('interest on ' + packet.name + ' arrives at ' + env.now.__str__())
        print("cache miss, pit miss")
        forwarder.get_default_tier().cmr += 1

        # add entry to the pit
        forwarder.pit.add_to_pit(name, env.now + interest_life_time)

        # data won't return, forward interest
        if data_back == "i":
            print("packet loss")
            return

        # data will be returned, process data
        if data_back == "d":
            print("data is on its way")
            yield env.timeout(response_time)
            if priority == 'l':
                forwarder.get_default_tier().low_p_data_retrieval_time += Decimal(env.now) - timestamp
            else:
                forwarder.get_default_tier().high_p_data_retrieval_time += Decimal(env.now) - timestamp
            forwarder.get_default_tier().time_spent_reading += env.now

            print("=========")
            print(packet.name + ', data arrives at ' + env.now.__str__())
            if not forwarder.pit.pit_has_name(name):
                print("data already came")
                return
            if forwarder.pit.get_pit_entry(name) > env.now:
                print("pit for the data expired")
                forwarder.pit.del_from_pit(name)
                return

            # write data to default-tier
            print("write to default-tier")
            tier = forwarder.get_default_tier()
            tier.write_packet(env, res, packet)
            # delete pit entry
            forwarder.pit.del_from_pit(name)
        else:
            raise RuntimeError(f'Unknown operation code {type}')

    @property
    def column_names(self):
        return self._COLUMN_NAMES
