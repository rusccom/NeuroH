"""Memory protocols used by higher layers."""

from __future__ import annotations

from typing import Protocol

from homeoorganism.v1_baseline.agent.belief_map import BeliefMap
from homeoorganism.domain.enums import BiomeId, ResourceType
from homeoorganism.domain.types import Pose, ReplaySample, TargetProposal


class FastMemoryReader(Protocol):
    def query(
        self,
        rtype: ResourceType,
        from_pose: Pose,
        step_idx: int,
    ) -> TargetProposal | None: ...


class SlowMemoryReader(Protocol):
    def query(
        self,
        biome_id: BiomeId,
        rtype: ResourceType,
        belief_map: BeliefMap,
    ) -> TargetProposal | None: ...

    def update(self, samples: list[ReplaySample]) -> None: ...
