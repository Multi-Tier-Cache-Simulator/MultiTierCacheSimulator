import simpy

from common.deque import Deque
from forwarder_structures.content_store.tier import Tier


class Index:
    # add the time of writing to the index as well ?
    def __init__(self, env):
        self.mutex = simpy.Resource(env, capacity=1)  # mutex on the index of capacity
        self.active_index = dict()  # key: packet_name, value: tier
        self.ghost_index = dict()  # key: packet_name, value: b1 or b2
        self._b1 = Deque()
        self._b2 = Deque()

    def __str__(self, what='index'):
        if what == 'index':
            print("Active Index:")
            for packet_name, tier in self.active_index.items():
                print(f"{packet_name}:{tier.name}", end=", ")
            print(" ")
        else:
            print("Ghost Index:")
            for packet_name, queue_name in self.ghost_index.items():
                print(f"{packet_name}:{queue_name}", end=", ")
            print(" ")

    # Active Index
    def get_packet_tier(self, packet_name: str):
        with self.mutex.request() as req:
            yield req
            if packet_name in self.active_index.keys():
                return self.active_index[packet_name]
            else:
                raise ValueError(f"Packet {packet_name} not found in Content Store")

    def cs_has_packet(self, packet_name: str):
        """check if the packet exist in active index"""
        with self.mutex.request() as req:
            yield req
            return packet_name in self.active_index

    def packet_in_tier(self, packet_name: str, tier: Tier):
        """check if packet is in the tier"""
        with self.mutex.request() as req:
            yield req
            return self.active_index[packet_name] == tier

    def update_packet_tier(self, packet_name: str, tier: Tier):
        """update packet tier in the active index"""
        with self.mutex.request() as req:
            yield req
            self.active_index[packet_name] = tier

    def del_packet_from_cs(self, packet_name: str):
        """delete the packet from active index"""
        with self.mutex.request() as req:
            yield req
            self.active_index.pop(packet_name)

    # Ghost index
    def packet_in_ghost(self, packet_name: str, queue_name: str):
        """check if packet is in ghost index"""
        with self.mutex.request() as req:
            yield req
            if packet_name in self.ghost_index.keys():
                return self.ghost_index[packet_name] == queue_name
            else:
                return False

    def update_packet_ghost(self, packet_name: str, queue_name: str):
        """update packet in ghost index"""
        with self.mutex.request() as req:
            yield req
            if queue_name == "b1":
                self._b1.append_left(packet_name, packet_name)
            if queue_name == "b2":
                self._b2.append_left(packet_name, packet_name)
            self.ghost_index[packet_name] = queue_name

    def del_packet_from_ghost(self, packet_name: str):
        """delete the packet from ghost index"""
        with self.mutex.request() as req:
            yield req
            bi = self.ghost_index.get(packet_name)
            if bi == "b1":
                self._b1.remove(packet_name)
            if bi == "b2":
                self._b2.remove(packet_name)
            self.ghost_index.pop(packet_name)

    def pop_packet_from_ghost(self, queue_name: str):
        """pop the packet from the ghost index"""
        with self.mutex.request() as req:
            yield req
            if queue_name == "b1":
                packet_name = self._b1.pop()
            if queue_name == "b2":
                packet_name = self._b2.pop()
            self.ghost_index.pop(packet_name)

    def ghost_len(self, queue_name: str):
        """return the length of ghost packets in the queue"""
        with self.mutex.request() as req:
            yield req
            if queue_name == "b1":
                return len(self._b1)
            elif queue_name == "b2":
                return len(self._b2)
