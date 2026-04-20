"""Continuous-life monitoring snapshots."""

from __future__ import annotations

from pydantic import BaseModel

from homeoorganism.monitoring.domain.dto import StepSnapshot


class CompletedLifeSummary(BaseModel):
    life_id: int
    duration_ticks: int
    end_reason: str


class LifeSnapshot(StepSnapshot):
    life_id: int
    current_tick: int
    life_max_ticks: int
    completed_lives: list[CompletedLifeSummary]
    current_energy_ratio_100: float | None
    current_water_ratio_100: float | None
    current_deficit_variance: float | None
    long_window_energy_ratio: float | None
    long_window_water_ratio: float | None
    current_food_count: int
    current_water_count: int
    next_relocation_tick: int | None
