import csv
from resources import NDN_PACKETS
from storage_structures import Packet
from traces.trace import Trace


class NDNTrace(Trace):
    _COLUMN_NAMES = ("packetType", "timestamp", "name", "size", "priority", "responseTime ")

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

    def read_data_line(self, env, storage, line, tstart_tlast, logs_enabled=True):
        """Read a line, and fire events if necessary"""
        packetType, timestamp, name, size, priority, responseTime = line
        size = int(size)
        responseTime = float(responseTime)
        packet = Packet(packetType, name, size, priority)
        # if data packet --> write it in the default tier
        print("////////////////////////////////////")
        if packetType == "d":
            print("data packet = " + name)
            if name in storage.index.index:
                print("ndn-trace, data already in cache")
                return
            # write data to default-tier
            tier = storage.get_default_tier()
            tier.write_packet(tstart_tlast, packet)
        # if interest packet
        elif packetType == "i":
            print("interest packet = " + name)
            tier = storage.index.get_packet_tier(name)
            # if data not in cache --> cache miss
            if tier == -1:
                print("cache miss")
                storage.get_default_tier().cmr += 1
                storage.get_default_tier().time_spent_reading += responseTime / 10 ** 9
            # if data not in default tier --> migrate data to default tier
            # read the packet
            else:
                if tier.name.__str__() != storage.get_default_tier().name.__str__():
                    print("read from disk")
                    tier.read_packet(tstart_tlast, packet)
                    # delete name in nvme
                    tier.prefetch_packet(packet)
                    storage.get_default_tier().write_packet(tstart_tlast, packet, cause='prefetching')
                    print("Prefetch data to default tier " + storage.get_default_tier().name.__str__())
                else:
                    print("read from dram")
                    tier.read_packet(tstart_tlast, packet)
        else:
            raise RuntimeError(f'Unknown operation code {type}')

    def timestamp_from_line(self, line):
        return int(line[1])

    @property
    def column_names(self):
        return self._COLUMN_NAMES
