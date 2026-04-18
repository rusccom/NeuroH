"""Thread-safe run state store."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import monotonic

from homeoorganism.monitoring.domain.enums import RunState


@dataclass
class RunStateStore:
    run_state: RunState = RunState.IDLE
    episode_id: int = 0
    debug_enabled: bool = False
    _lock: Lock = field(default_factory=Lock)
    _started_at: float = field(default_factory=monotonic)

    def set_state(self, run_state: RunState) -> None:
        with self._lock:
            self.run_state = run_state

    def get_run_state(self) -> RunState:
        with self._lock:
            return self.run_state

    def set_episode(self, episode_id: int) -> None:
        with self._lock:
            self.episode_id = episode_id

    def get_episode(self) -> int:
        with self._lock:
            return self.episode_id

    def toggle_debug(self, enabled: bool | None = None) -> bool:
        with self._lock:
            self.debug_enabled = not self.debug_enabled if enabled is None else enabled
            return self.debug_enabled

    def is_debug(self) -> bool:
        with self._lock:
            return self.debug_enabled

    def elapsed_sec(self) -> float:
        return monotonic() - self._started_at
