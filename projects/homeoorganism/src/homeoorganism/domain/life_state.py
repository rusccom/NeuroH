"""Life-level runtime state."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LifeState:
    life_id: int
    tick: int
    started_at_ts_ms: int
    ended_at_ts_ms: int | None
    end_reason: str | None
