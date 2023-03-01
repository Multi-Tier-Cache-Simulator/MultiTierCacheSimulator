from collections import OrderedDict


class Deque(object):
    """Fast searchable queue for default-tier"""

    def __init__(self):
        self.od = OrderedDict()

    def __str__(self):
        for key, value in self.od.items():
            print(key.__str__() + ", ", end="")
        print(" ")

    def __len__(self):
        return len(self.od)

    def __contains__(self, k):
        return k in self.od

    def __index__(self, key):
        # convert the ordered dictionary to a list
        keys = list(self.od.keys())
        print("here", keys.__str__())
        return keys.index(key)

    def update(self, ti):
        return self.od.update(ti)

    def append_by_index(self, index, key, value):
        if key in self.od:
            del self.od[key]
        # convert the ordered dictionary to a list
        items = list(self.od.items())
        # insert a new element at index 1
        items.insert(index, (key, value))
        self.od = OrderedDict(items)

    def append_left(self, key, value):
        if key in self.od:
            del self.od[key]
        self.od[key] = value

    def pop(self):
        return self.od.popitem(0)[1]

    def remove(self, k):
        del self.od[k]

    def get_without_pop(self):
        return next(iter(self.od.items()))

    def items(self):
        return self.od.items()
