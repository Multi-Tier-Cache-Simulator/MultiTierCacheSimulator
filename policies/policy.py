from storage_structures import StorageManager, Tier
from simpy.core import Environment


class Policy:
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        self.tier = tier
        self.storage = storage
        self.env = env
        tier.register_listener(self)

    def on_packet_access(self, timestamp: int, name: str, size: int, priority: str, isWrite: bool):
        pass
