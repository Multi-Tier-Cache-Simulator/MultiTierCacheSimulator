from forwarder_structures import Forwarder, Tier
from simpy.core import Environment


class Policy:

    def __init__(self, env: Environment, forwarder: Forwarder, tier: Tier):
        self.env = env
        self.forwarder = forwarder
        self.tier = tier
        tier.register_listener(self)
