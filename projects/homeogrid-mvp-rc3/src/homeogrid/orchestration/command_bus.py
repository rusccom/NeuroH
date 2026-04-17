"""Operator command bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Queue

from homeogrid.monitoring.domain.enums import OperatorCommandType


@dataclass
class QueuedCommand:
    command_type: OperatorCommandType
    enabled: bool | None = None


@dataclass
class CommandBus:
    max_size: int = 256
    _queue: Queue = field(init=False)

    def __post_init__(self) -> None:
        self._queue = Queue(maxsize=self.max_size)

    def submit(self, command_type: OperatorCommandType, enabled: bool | None = None) -> bool:
        if self._queue.full():
            return False
        self._queue.put_nowait(QueuedCommand(command_type, enabled))
        return True

    def drain(self) -> list[QueuedCommand]:
        commands = []
        while True:
            try:
                commands.append(self._queue.get_nowait())
            except Empty:
                return commands
