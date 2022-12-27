from simpy.core import Environment
from typing import List
from forwarder_structures.pit import PIT
from forwarder_structures.tier import Tier
from forwarder_structures.index import Index


class Forwarder:
    def __init__(self, env: Environment, index: Index, tiers: List[Tier], pit: PIT, slot_size: int,
                 default_tier_index: int = 0):
        self._env = env

        # content store
        # index
        self.index = index
        # tiers
        self.tiers = tiers

        # pit table
        self.pit = pit

        # number of aggregation
        self.nAggregation = 0

        # default tier
        self.default_tier_index = default_tier_index

        # slot size
        self.slot_size = slot_size

        # association linking
        for tier in tiers:
            tier.forwarder = self

    def get_default_tier(self):
        return self.tiers[self.default_tier_index]
