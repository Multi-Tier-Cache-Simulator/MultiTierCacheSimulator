from storage_structures import StorageManager, Tier
from simpy.core import Environment


class Policy:
    def __init__(self, tier: Tier, storage: StorageManager, env: Environment):
        self.tier = tier
        self.storage = storage
        self.env = env
        tier.register_listener(self)


