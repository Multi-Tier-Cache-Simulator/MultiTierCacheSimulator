from forwarder_structures.content_store.tier import Tier


class Index:
    # add the time of writing to the index as well ?
    def __init__(self):
        self.active_index = dict()  # key: packet_name, value: tier
        self.ghost_index = dict()  # key: packet_name, value: b1 or b2

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
        if packet_name in self.active_index.keys():
            return self.active_index[packet_name]
        else:
            raise ValueError(f"Packet {packet_name} not found in Content Store")

    def cs_has_packet(self, packet_name: str) -> bool:
        """check if the packet exist in active index"""
        return packet_name in self.active_index

    def packet_in_tier(self, packet_name: str, tier: Tier) -> bool:
        """check if packet is in the tier"""
        return self.active_index[packet_name] == tier

    def update_packet_tier(self, packet_name: str, tier: Tier):
        """update packet tier in the active index"""
        self.active_index[packet_name] = tier

    def del_packet_from_cs(self, packet_name: str):
        """delete the packet from active index"""
        self.active_index.pop(packet_name)

    # Ghost index
    def packet_in_ghost(self, packet_name: str, queue_name: str) -> bool:
        """check if packet is in ghost index"""
        if packet_name in self.ghost_index.keys():
            return self.ghost_index[packet_name] == queue_name
        else:
            return False

    def update_packet_ghost(self, packet_name: str, queue_name: str):
        """update packet in ghost index"""
        self.ghost_index[packet_name] = queue_name

    def del_packet_from_ghost(self, packet_name: str):
        """delete the packet from ghost index"""
        self.ghost_index.pop(packet_name)

    def pop_packet_from_ghost(self, queue_name: str):
        """pop the packet from the ghost index"""
        q_name = [packet_name for packet_name in self.ghost_index.keys() if
                  self.ghost_index[packet_name] == queue_name]
        if not q_name:
            raise ValueError(f"No packets found in {queue_name} queue")
        packet_name = q_name[0]
        self.ghost_index.pop(packet_name)

    def ghost_len(self, queue_name: str):
        """return the length of ghost packets in the queue"""
        return len([packet_name for packet_name in self.ghost_index.keys() if
                    self.ghost_index[packet_name] == queue_name])
