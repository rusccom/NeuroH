"""Body configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BodyConfig:
    energy_start: int = 70
    water_start: int = 70
    energy_max: int = 100
    water_max: int = 100
    base_energy_cost: int = 1
    base_water_cost: int = 1
    move_extra_energy_cost: int = 1
    rough_extra_energy_cost: int = 2
    rough_extra_water_cost: int = 1
    low_state_threshold: int = 15
    low_state_move_extra_energy_cost: int = 1
    interact_gain: int = 35
