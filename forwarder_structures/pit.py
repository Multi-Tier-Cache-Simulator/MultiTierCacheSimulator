from simpy import Environment


class PIT:
    def __init__(self):
        self.pit = dict()  # key: packet_name, value: expiration_time

    def __str__(self):
        for packet_name, expiration_time in self.pit.items():
            print(packet_name + ":" + expiration_time.__str__(), end=", ")
        print(" ")

    def pit_has_name(self, packet_name: str):
        if packet_name in self.pit:
            return True
        else:
            return False

    def get_pit_entry(self, packet_name: str):
        return self.pit[packet_name]

    def add_to_pit(self, packet_name: str, expiration_time: int):
        self.pit[packet_name] = expiration_time

    def del_from_pit(self, packet_name: str):
        self.pit.pop(packet_name)

    def update_pit_times(self, env: Environment):
        self.pit = {packet_name: expiration_time for packet_name, expiration_time in self.pit.items() if
                    self.get_pit_entry(packet_name) > env.now}
