"""Planner configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlannerConfig:
    turn_cost: float = 0.2
    rough_cost: float = 3.0
    unknown_cost: float = 1.5
    max_plan_len: int = 64
