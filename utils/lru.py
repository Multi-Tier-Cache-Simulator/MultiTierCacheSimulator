from collections import OrderedDict


class LRU:
    def __init__(self, capacity: int):
        self.lru_dict = OrderedDict()
        self.nb_packets_capacity = capacity

    def get(self, key: str) -> int:
        if key not in self.lru_dict:
            return -1
        else:
            self.lru_dict.move_to_end(key)
            return self.lru_dict[key]

    # name size
    def put(self, key: str, value: int) -> None:
        if len(self.lru_dict) >= self.nb_packets_capacity:
            self.lru_dict.popitem(last=False)
        self.lru_dict[key] = value


cache = LRU(1000)

hit = 0
miss = 0

with open("ndn_trace.csv", "r") as trace_file:
    i = 0
    for line in trace_file:
        i += 1
        request = line.strip().split(',')
        req_time = request[1]
        name = request[2]
        size = int(request[3])
        priority = request[4]
        lifetime = request[5]
        response_time = request[6]
        # print(name)

        if cache.get(name) != -1:
            hit += 1
            # print(name.__str__()+" hit")
        else:
            miss += 1
            # print(name.__str__() + " miss")
            cache.put(name, size)
        # print(cache.lru_dict.__str__())
    # print(i)
    # print(hit)
    # print(miss)
    # print(miss + hit)

hit_rate = hit / (hit + miss)
print("lru Cache hit rate: {:.2f}%".format(hit_rate * 100))
