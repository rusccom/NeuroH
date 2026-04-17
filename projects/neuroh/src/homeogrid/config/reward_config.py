"""Reward configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RewardConfig:
    energy_setpoint: int = 70
    water_setpoint: int = 70
    weight_energy: float = 0.5
    weight_water: float = 0.5
    action_cost_weight: float = 0.02
    collision_penalty: float = 0.2
    death_penalty: float = 5.0
