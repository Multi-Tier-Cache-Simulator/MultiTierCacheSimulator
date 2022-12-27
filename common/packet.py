class Packet:
    def __init__(self, data_back, timestamp, name, size, priority):
        self.data_back = data_back
        self.name = name
        self.size = size
        self.priority = priority
        self.timestamp = timestamp

    def __str__(self):
        print(self.data_back.__str__() + ", " + self.name.__str__() + ", " + self.size.__str__() + ", ")
