from forwarder_structures.content_store.tier import Tier
from forwarder import Forwarder
from simpy.core import Environment


class Policy:

    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        self.env = env
        self.forwarder = forwarder
        self.tier = tier
        tier.register_listener(self)
