from tier import Tier


class Index:
    # add the time of writing to the index as well ?
    def __init__(self):
        self.active_index = dict()  # key: packet_name, value: tier
        self.ghost_index = dict()  # key: packet_name, value: b1 or b2

    def __str__(self, what='index'):
        if what == 'index':
            print("index")
            for packet_name, tier in self.active_index.items():
                print(packet_name + ':' + tier.name, end=", ")
            print(" ")
        else:
            print("ghost index")
            for packet_name, queue_name in self.ghost_index.items():
                print(packet_name + ':' + queue_name, end=", ")
            print(" ")

    # index
    def get_packet_tier(self, packet_name: str):
        if packet_name in self.active_index.keys():
            return self.active_index[packet_name]
        else:
            print('packet not in cs')
            return -1

    def cs_has_packet(self, packet_name: str):
        if packet_name in self.active_index:
            return True
        else:
            return False

    def packet_in_tier(self, packet_name: str, tier: Tier):
        if self.active_index[packet_name] == tier:
            return True
        else:
            return False

    def update_packet_tier(self, packet_name: str, tier: Tier):
        self.active_index[packet_name] = tier

    def del_packet_from_cs(self, packet_name: str):
        self.active_index.pop(packet_name)

    # ghost index
    def packet_in_ghost(self, packet_name: str, queue_name: str):
        if packet_name in self.ghost_index.keys():
            if self.ghost_index[packet_name] == queue_name:
                return True
            else:
                return False
        else:
            return False

    def update_packet_ghost(self, packet_name: str, queue_name: str):
        self.ghost_index[packet_name] = queue_name

    def del_packet_from_ghost(self, packet_name: str):
        self.ghost_index.pop(packet_name)

    def pop_packet_from_ghost(self, queue_name: str):
        q_name = [packet_name for packet_name in self.ghost_index.keys() if
                  self.ghost_index[packet_name] == queue_name]
        packet_name = q_name[0]
        self.ghost_index.pop(packet_name)

    def ghost_len(self, queue_name: str):
        return len([packet_name for packet_name in self.ghost_index.keys() if
                    self.ghost_index[packet_name] == queue_name])
