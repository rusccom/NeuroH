"""Continuous run result."""

from dataclasses import dataclass
from pathlib import Path

from homeoorganism.domain.life_state import LifeState


@dataclass(frozen=True)
class RunReport:
    mode: str
    seed: int
    requested_lives: int
    completed_lives: int
    root_dir: Path
    life_states: tuple[LifeState, ...]
