"""Ecology configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EcologyConfig:
    food_regen_mean_ticks: int = 35
    water_regen_mean_ticks: int = 35
    food_target_count: int = 2
    water_target_count: int = 2
    regen_jitter: float = 0.25
    resource_ttl_ticks: int | None = None
    relocation_period_ticks: int = 1000
    relocation_probability: float = 0.5
