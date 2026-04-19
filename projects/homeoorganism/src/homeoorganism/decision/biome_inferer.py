"""Biome inference from landmarks."""

from dataclasses import dataclass

import numpy as np

from homeoorganism.agent.belief_map import BeliefMap
from homeoorganism.domain.enums import BiomeId
from homeoorganism.domain.types import Observation


LANDMARK_TO_BIOME = {
    1: BiomeId.A,
    2: BiomeId.B,
    3: BiomeId.C,
    4: BiomeId.D,
}


@dataclass
class BiomeInferer:
    current_biome: BiomeId | None = None

    def reset(self) -> None:
        self.current_biome = None

    def infer(self, obs: Observation, belief_map: BeliefMap) -> BiomeId | None:
        landmark_ids = obs.landmark_ids[obs.landmark_ids > 0]
        if landmark_ids.size == 0:
            return self.current_biome
        landmark_id = int(np.unique(landmark_ids)[0])
        self.current_biome = LANDMARK_TO_BIOME.get(landmark_id)
        return self.current_biome

