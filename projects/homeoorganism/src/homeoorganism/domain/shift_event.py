"""Continuous-life perturbation events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ShiftEvent:
    life_id: int
    tick: int
    event_type: str
    success: bool
