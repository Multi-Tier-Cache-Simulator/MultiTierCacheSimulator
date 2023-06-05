import csv

from common.packet import Packet
from common.penalty import get_penalty
from resources import NDN_PACKETS
from traces.trace_reading.trace import Trace


class CommonTrace(Trace):
    _COLUMN_NAMES = ("data_back", "timestamp", "name", "size", "priority", "InterestLifetime", "responseTime")

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

    def read_data_line(self, env, name_lock, res, forwarder, line, log_file, logs_enabled=True):
        """Read a line, and fire events if necessary"""
        data_back, timestamp, name, size, priority, interest_life_time, response_time = line
        timestamp = float(timestamp)
        size = int(size)
        interest_life_time = float(interest_life_time)
        response_time = float(response_time)

        # create the packet
        packet = Packet(data_back, timestamp, name, size, priority)

        # update the pit table entries by deleting the expired ones
        forwarder.pit.update_times(env)

        with name_lock.request() as lock:
            yield lock
            # index lookup
            in_index = yield env.process(forwarder.index.cs_has_packet(name))

            # cache hit
            if in_index:
                tier = yield env.process(forwarder.index.get_packet_tier(name))
                print("cache hit, read packet %s from tier %s" % (name, tier.name))

                yield env.process(tier.read_packet(env, res, packet))

                # chr
                tier.chr += 1
                if priority == 'h':
                    tier.chr_hpc += 1
                else:
                    if priority == 'l':
                        tier.chr_lpc += 1

                # data in disk
                if tier.name.__str__() != forwarder.get_default_tier().name.__str__():
                    print("prefetch data to default tier " + forwarder.get_default_tier().name.__str__())

                    # hit in disk apply penalty
                    if priority == 'h':
                        forwarder.get_default_tier().penalty_hpc += get_penalty(0.0, priority)
                    elif priority == 'l':
                        forwarder.get_default_tier().penalty_lpc += get_penalty(0.0, priority)

                    # prefetch data to default-tier
                    yield env.process(tier.prefetch_packet(env, packet))
                    yield env.process(forwarder.get_default_tier().write_packet(env, res, packet, cause="prefetching"))
                return

        # cache miss and pit hit
        if forwarder.pit.has_name(name):
            print("cache miss, pit hit")
            forwarder.get_default_tier().cmr += 1
            # add penalty for the remaining time to have the data back
            # remaining_time = response_time - (req_i_arrival - req_i-1_arrival)
            remaining_time = response_time - (timestamp - (forwarder.pit.retrieve_entry(name) - interest_life_time))
            if priority == 'h':
                forwarder.get_default_tier().cmr_hpc += 1
                forwarder.get_default_tier().penalty_hpc += get_penalty(remaining_time, priority)
            elif priority == 'l':
                forwarder.get_default_tier().cmr_lpc += 1
                forwarder.get_default_tier().penalty_lpc += get_penalty(remaining_time, priority)
            forwarder.pit.add_entry(name, env.now + interest_life_time)
            forwarder.nAggregation += 1
            return

        # cache miss and pit miss
        print("cache miss, pit miss")
        # add entry to the pit
        forwarder.pit.add_entry(name, env.now + interest_life_time)
        forwarder.get_default_tier().cmr += 1
        if priority == 'h':
            forwarder.get_default_tier().cmr_hpc += 1
            forwarder.get_default_tier().penalty_hpc += get_penalty(response_time, priority)
        elif priority == 'l':
            forwarder.get_default_tier().cmr_lpc += 1
            forwarder.get_default_tier().penalty_lpc += get_penalty(response_time, priority)

        print("%s data is on its way" % name)
        yield env.timeout(response_time)

        with name_lock.request() as lock:
            yield lock
            print("///////////")
            print('%s data arrives at %s ' % (name, env.now))

            if not forwarder.pit.has_name(name):
                print("%s data already came" % name)
                return

            if forwarder.pit.retrieve_entry(name) < env.now:
                print("interest on %s expired" % name)
                forwarder.pit.delete_entry(name)
                return

            # delete pit entry
            forwarder.pit.delete_entry(name)
            in_index = yield env.process(forwarder.index.cs_has_packet(name))
            if in_index:
                print("%s data already in cs" % name)
            else:
                # write data to default-tier
                print("%s write to default-tier" % packet.name)
                yield env.process(forwarder.get_default_tier().write_packet(env, res, packet))

    @property
    def column_names(self):
        return self._COLUMN_NAMES
