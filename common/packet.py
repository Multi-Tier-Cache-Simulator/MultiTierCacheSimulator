class Packet:
    def __init__(self, data_back: str, timestamp: float, name: str, size: int, priority: str):
        self.data_back = data_back
        self.timestamp = timestamp
        self.name = name
        self.size = size
        self.priority = priority

    def __str__(self):
        return f'Packet, Name: {self.name}, Size: {self.size}, Priority: {self.priority}, Timestamp: {self.timestamp}'
