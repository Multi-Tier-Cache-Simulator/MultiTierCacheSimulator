from collections import deque


class ARC:
    def __init__(self, c):
        self.c = c  # Cache size
        self.cached = {}  # Cached keys
        self.p = 0
        self.t1 = deque()
        self.t2 = deque()
        self.b1 = deque()
        self.b2 = deque()

    def replace(self, args):
        if self.t1 and ((args in self.b2 and len(self.t1) == self.p) or (len(self.t1) > self.p)):
            old = self.t1.pop()
            self.b1.appendleft(old)
        else:
            old = self.t2.pop()
            self.b2.appendleft(old)
        del self.cached[old]

    def get(self, key):
        if key in self.t1:
            self.t1.remove(key)
            self.t2.appendleft(key)
            return 1
        elif key in self.t2:
            self.t2.remove(key)
            self.t2.appendleft(key)
            return 1
        return -1

    def put(self, key):
        if key in self.cached:
            return
        self.cached[key] = 1
        if key in self.b1:
            self.p = min(self.c, self.p + max(len(self.b2) / len(self.b1), 1))
            self.replace(key)
            self.b1.remove(key)
            self.t2.appendleft(key)
            return
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) / len(self.b2), 1))
            self.replace(key)
            self.b2.remove(key)
            self.t2.appendleft(key)
            return
        if len(self.t1) + len(self.b1) == self.c:
            if len(self.t1) < self.c:
                self.b1.pop()
                self.replace(key)
            else:
                del self.cached[self.t1.pop()]
        else:
            total = len(self.t1) + len(self.b1) + len(self.t2) + len(self.b2)
            if total >= self.c:
                if total == (2 * self.c):
                    self.b2.pop()
                self.replace(key)
        self.t1.appendleft(key)


cachearc = ARC(1000)

hit = 0
miss = 0

with open("ndn_trace.csv", "r") as trace_file:
    for line in trace_file:
        request = line.strip().split(',')
        req_time = request[1]
        name = request[2]
        size = int(request[3])
        priority = request[4]
        lifetime = request[5]
        response_time = request[6]

        if cachearc.get(name) != -1:
            # print(name + ", hit")
            hit += 1
        else:
            miss += 1
            # print(name + ", miss")
            cachearc.put(name)

hit_rate = hit / (hit + miss)
print("arc Cache hit rate: {:.2f}%".format(hit_rate * 100))