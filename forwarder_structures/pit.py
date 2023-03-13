from typing import Dict

from simpy import Environment


class PIT:
    def __init__(self):
        self.pit: Dict[str, int] = dict()  # key: packet_name, value: expiration_time

    def __str__(self):
        for packet_name, expiration_time in self.pit.items():
            print(packet_name + ":" + expiration_time.__str__(), end=", ")
        print(" ")

    def has_name(self, packet_name: str) -> bool:
        return packet_name in self.pit

    def retrieve_entry(self, packet_name: str) -> int:
        return self.pit[packet_name]

    def add_entry(self, packet_name: str, expiration_time: int):
        self.pit[packet_name] = expiration_time

    def delete_entry(self, packet_name: str):
        self.pit.pop(packet_name)

    def update_times(self, env: Environment):
        self.pit = {packet_name: expiration_time for packet_name, expiration_time in self.pit.items() if
                    self.retrieve_entry(packet_name) > env.now}
