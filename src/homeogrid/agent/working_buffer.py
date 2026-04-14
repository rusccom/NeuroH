"""Current decision state buffer."""

from dataclasses import dataclass, field

from homeogrid.domain.types import Plan, WorkingMemoryState


@dataclass
class WorkingBuffer:
    state: WorkingMemoryState = field(default_factory=WorkingMemoryState)

    def reset(self) -> None:
        self.state = WorkingMemoryState(current_plan=Plan(valid=False))
