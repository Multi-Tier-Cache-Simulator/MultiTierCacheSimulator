import csv
from resources import NDN_PACKETS
from traces.trace import Trace


class NDNTrace(Trace):
    _COLUMN_NAMES = ("packetType", "timestamp", "name", "size", "priority")

    def __init__(self):
        Trace.__init__(self)
        self.data = []

    def gen_data(self, trace_len_limit=-1):
        for path in NDN_PACKETS:
            with open(path) as read_obj:
                csv_reader = csv.reader(read_obj)
                self.data = list(csv_reader)
                if trace_len_limit > 0:
                    self.data = self.data[:min(len(self.data), trace_len_limit)]

    def read_data_line(self, env, storage, line, tstart_tlast, logs_enabled=True):
        """Read a line, and fire events if necessary"""
        packetType, timestamp, name, size, priority, responseTime = line

        timestamp = int(timestamp)
        size = int(size)
        responseTime = int(responseTime)

        # if data packet --> write it in the default tier
        if packetType == "d":
            tier = storage.get_default_tier()
            tier.write_packet(timestamp, tstart_tlast, name, size, priority)
        elif packetType == "i":
            tier = storage.index.get_packet_tier(name)
            if tier == -1:  # if data not in cache --> cache miss
                print("\"" + name.__str__() + "\" cache miss")
                storage.get_default_tier().cmr += 1
                storage.get_default_tier().time_spent_reading += responseTime
            else:  # if data not in default tier --> migrate data to default tier
                if tier.name.__str__() != storage.get_default_tier().name.__str__():
                    tier.number_of_prefetching_from_this_tier += 1
                    storage.get_default_tier().number_of_prefetching_to_this_tier += 1
                    storage.get_default_tier().write_packet(timestamp, tstart_tlast, name, size, priority)
                    print(
                        "Migrate \"" + name.__str__() + "\" to default tier " + storage.get_default_tier().name.__str__())
                else:  # else read
                    tier.read_packet(timestamp, tstart_tlast, name, size, priority)
        else:
            raise RuntimeError(f'Unknown operation code {type}')

    def timestamp_from_line(self, line):
        return int(line[1])

    @property
    def column_names(self):
        return self._COLUMN_NAMES
