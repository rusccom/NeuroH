"""Replay sample construction."""

from dataclasses import dataclass

from homeoorganism.domain.enums import EventType
from homeoorganism.domain.types import ReplaySample, SalientEvent


@dataclass
class ReplayManager:
    def build_samples(self, events: list[SalientEvent]) -> list[ReplaySample]:
        return [self._to_sample(event) for event in events if self._should_keep(event)]

    def _should_keep(self, event: SalientEvent) -> bool:
        if event.position is None or event.resource_type is None or event.biome_id is None:
            return False
        return event.event_type in {
            EventType.RESOURCE_OBSERVED,
            EventType.RESOURCE_CONSUMED,
            EventType.RESOURCE_RELOCATED,
        }

    def _to_sample(self, event: SalientEvent) -> ReplaySample:
        return ReplaySample(
            biome_id=event.biome_id,
            resource_type=event.resource_type,
            position=event.position,
            weight=event.salience,
        )

