import collections


class LFU:
    def __init__(self, c):
        # c is cache size
        self.nb_packets_capacity = c
        self.freqToKey = collections.defaultdict(dict)  # frequency to dict of <key, val>
        self.keyToFreq = collections.defaultdict(int)
        self.keyToVal = collections.defaultdict(int)

    def get(self, key):
        if key in self.keyToVal:
            curr_freq = self.keyToFreq[key]
            self.freqToKey[curr_freq].pop(key)
            self.freqToKey[curr_freq + 1][key] = key
            self.keyToFreq[key] = curr_freq + 1
            return 1
        else:
            return -1

    def put(self, key, val=1):
        def first(inp):
            return next(iter(inp))

        if key in self.keyToVal:
            curr_freq = self.keyToFreq[key]
            self.freqToKey[curr_freq].pop(key)
            self.freqToKey[curr_freq + 1][key] = key
            self.keyToFreq[key] = curr_freq + 1
            self.keyToVal[key] = key
        else:
            if len(self.keyToVal) >= self.nb_packets_capacity:
                # print("evict from the Others")
                # need to pop out <key,value> with the smallest frequency
                freq = 1
                while len(self.freqToKey[freq]) == 0:
                    freq += 1

                first_key = first(self.freqToKey[freq])
                self.freqToKey[freq].pop(first_key)
                del self.keyToFreq[first_key]
                old = self.keyToVal[first_key]
                del self.keyToVal[first_key]

            self.freqToKey[1][key] = key
            self.keyToFreq[key] = 1
            self.keyToVal[key] = key


cachelfu = LFU(200)

hit = 0
miss = 0

with open("../../resources/other_dataset/lru_better.csv", "r") as trace_file:
    for line in trace_file:
        request = line.strip().split(',')
        req_time = request[1]
        name = int(request[2])
        size = int(request[3])
        priority = request[4]
        lifetime = request[5]
        response_time = request[6]

        if cachelfu.get(name) != -1:
            hit += 1
            # print(name.__str__()+" hit")
        else:
            miss += 1
            # print(name.__str__() + " miss")
            cachelfu.put(name, size)
        # print(cachelfu.keyToVal.__str__())

hit_rate = hit / (hit + miss)
print("lfu Cache hit rate: {:.2f}%".format(hit_rate * 100))
