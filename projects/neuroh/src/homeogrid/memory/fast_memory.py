"""Fast episode memory."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from homeogrid.config.memory_config import MemoryConfig
from homeogrid.domain.enums import ResourceType, TargetSource
from homeogrid.domain.types import Pose, SalientEvent, TargetProposal, Vec2


@dataclass
class ResourceTrace:
    resource_type: ResourceType
    position: Vec2
    step_seen: int
    last_confirmed_step: int
    valid: bool
    confidence: float


@dataclass
class FastMemory:
    memory_config: MemoryConfig
    enabled: bool = True

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._traces: dict[tuple[ResourceType, int, int], ResourceTrace] = {}
        self._events: deque[SalientEvent] = deque(maxlen=self.memory_config.fast_max_events)

    def observe_resource(self, rtype: ResourceType, pos: Vec2, step_idx: int) -> None:
        key = (rtype, pos.x, pos.y)
        self._traces[key] = ResourceTrace(rtype, pos, step_idx, step_idx, True, 1.0)

    def invalidate_resource(self, rtype: ResourceType, pos: Vec2, step_idx: int) -> None:
        trace = self._traces.get((rtype, pos.x, pos.y))
        if trace is None:
            return
        trace.valid = False
        trace.confidence = 0.0
        trace.last_confirmed_step = step_idx

    def query(self, rtype: ResourceType, from_pose: Pose, step_idx: int) -> TargetProposal | None:
        if not self.enabled:
            return None
        scored = self._score_traces(rtype, from_pose, step_idx)
        if not scored:
            return None
        score, trace = max(scored, key=lambda item: item[0])
        return TargetProposal(
            source=TargetSource.FAST,
            resource_type=rtype,
            confidence=score,
            exact_cell=trace.position,
        )

    def write_event(self, event: SalientEvent) -> None:
        self._events.append(event)

    def export_events(self) -> list[SalientEvent]:
        return list(self._events)

    def _score_traces(
        self,
        rtype: ResourceType,
        from_pose: Pose,
        step_idx: int,
    ) -> list[tuple[float, ResourceTrace]]:
        result = []
        for trace in self._traces.values():
            if trace.resource_type != rtype or not trace.valid:
                continue
            freshness = max(
                0.0,
                1.0 - (step_idx - trace.last_confirmed_step) / self.memory_config.fast_max_age,
            )
            distance = abs(from_pose.x - trace.position.x) + abs(from_pose.y - trace.position.y)
            score = 0.7 * freshness + 0.3 * (1.0 / (1 + distance))
            result.append((score, trace))
        return result
