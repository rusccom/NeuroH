"""Reward model."""

from dataclasses import dataclass

from homeogrid.config.reward_config import RewardConfig
from homeogrid.domain.types import BodyState, StepInfo


@dataclass
class RewardModel:
    reward_config: RewardConfig

    def compute(self, body: BodyState, info: StepInfo) -> float:
        energy_gap = max(0, self.reward_config.energy_setpoint - body.energy)
        water_gap = max(0, self.reward_config.water_setpoint - body.water)
        d_energy = energy_gap / self.reward_config.energy_setpoint
        d_water = water_gap / self.reward_config.water_setpoint
        reward = -(self.reward_config.weight_energy * d_energy)
        reward -= self.reward_config.weight_water * d_water
        reward -= self.reward_config.action_cost_weight * (
            info.action_cost_energy + info.action_cost_water
        )
        reward -= self.reward_config.collision_penalty if info.collision else 0.0
        reward -= self.reward_config.death_penalty if info.death_reason else 0.0
        return reward
