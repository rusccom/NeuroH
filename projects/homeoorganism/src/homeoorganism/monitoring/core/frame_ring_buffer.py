"""Frame ring buffer."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class FrameRingBuffer:
    max_size: int
    _frames: deque = field(init=False)
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        self._frames = deque(maxlen=self.max_size)

    def append(self, frame) -> None:
        with self._lock:
            self._frames.append(frame)

    def latest(self):
        with self._lock:
            return self._frames[-1] if self._frames else None

    def tail(self, count: int) -> list:
        with self._lock:
            return list(self._frames)[-count:]
