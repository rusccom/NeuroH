"""Mutable runtime state for a single life."""

from dataclasses import dataclass
from time import time_ns

from homeoorganism.domain.life_state import LifeState


@dataclass
class LifeRuntime:
    life_id: int
    tick: int = 0
    started_at_ts_ms: int = 0
    end_reason: str | None = None

    @classmethod
    def start(cls, life_id: int) -> "LifeRuntime":
        return cls(life_id=life_id, started_at_ts_ms=_current_ms())

    def advance(self, tick: int) -> None:
        self.tick = tick

    def finalize(self, end_reason: str | None) -> LifeState:
        self.end_reason = end_reason
        return LifeState(
            life_id=self.life_id,
            tick=self.tick,
            started_at_ts_ms=self.started_at_ts_ms,
            ended_at_ts_ms=_current_ms(),
            end_reason=end_reason,
        )


def _current_ms() -> int:
    return time_ns() // 1_000_000
