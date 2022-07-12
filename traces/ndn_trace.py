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

    def read_data_line(self, env, storage, line, logs_enabled=True):
        """Read a line, and fire events if necessary"""
        packetType, timestamp, name, size, priority, responseTime = line

        timestamp = int(timestamp)
        size = int(size)
        responseTime = int(responseTime)

        # if data packet --> write it in the default tier
        if packetType == "d":
            tier = storage.get_default_tier()
            tier.write_packet(timestamp, name, size, priority)
        elif packetType == "i":
            tier = storage.index.get_packet_tier(name)
            if tier == -1:  # if data not in cache --> cache miss
                print("\"" + name.__str__() + "\" cache miss")
            else:  # if data not in default tier --> migrate data to default tier
                if tier.name.__str__() != storage.get_default_tier().name.__str__():
                    print(tier)
                    print(storage.get_default_tier())
                    storage.migrate(timestamp, name, size, storage.get_default_tier())
                    print(
                        "Migrate \"" + name.__str__() + "\" to default tier " + storage.get_default_tier().name.__str__())
                else:  # else packet access
                    tier.read_packet(timestamp, name, size, priority)
        else:
            raise RuntimeError(f'Unknown operation code {type}')

    def timestamp_from_line(self, line):
        return int(line[1])

    @property
    def column_names(self):
        return self._COLUMN_NAMES
