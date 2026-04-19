"""Gymnasium-compatible environment wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import gymnasium as gym
import numpy as np

from homeoorganism.config.body_config import BodyConfig
from homeoorganism.config.ecology_config import EcologyConfig
from homeoorganism.config.env_config import EnvConfig
from homeoorganism.config.relocation_mode import RelocationMode
from homeoorganism.config.reward_config import RewardConfig
from homeoorganism.domain.enums import ActionType
from homeoorganism.domain.types import Observation, StepInfo
from homeoorganism.env.ecology import EcologyLayer, move_one_resource
from homeoorganism.env.observation_encoder import ObservationEncoder
from homeoorganism.env.physiology import PhysiologyModel
from homeoorganism.env.reward_model import RewardModel
from homeoorganism.env.world_generator import WorldGenerator
from homeoorganism.env.world_state import GridWorldState, clone_tiles


@dataclass
class HomeoGridEnv(gym.Env):
    env_config: EnvConfig
    body_config: BodyConfig
    reward_config: RewardConfig
    ecology_config: EcologyConfig = field(default_factory=EcologyConfig)

    metadata = {"render_modes": ["rgb_array"], "render_fps": 5}

    def __post_init__(self) -> None:
        self.generator = WorldGenerator(self.env_config, self.body_config)
        self.encoder = ObservationEncoder(self.env_config)
        self.physiology = PhysiologyModel(self.body_config)
        self.reward_model = RewardModel(self.reward_config)
        self.action_space = gym.spaces.Discrete(len(ActionType))
        self.observation_space = gym.spaces.Dict(
            {
                "tiles": gym.spaces.Box(-1, 5, (5, 5), dtype=np.int16),
                "landmark_ids": gym.spaces.Box(0, 4, (5, 5), dtype=np.int16),
                "pose": gym.spaces.Box(0, self.env_config.grid_size, (3,), dtype=np.int16),
                "body": gym.spaces.Box(0, 100, (4,), dtype=np.int16),
                "step_idx": gym.spaces.Discrete(self.env_config.episode_limit + 1),
            }
        )
        self.state: GridWorldState | None = None
        self._rng = np.random.default_rng()
        self.ecology = EcologyLayer(self.ecology_config, self._rng)
        self._relocation_done = False

    def reset(self, seed: int | None = None, options=None) -> tuple[Observation, dict]:
        super().reset(seed=seed)
        self._rng = np.random.default_rng(seed)
        self.ecology = EcologyLayer(self.ecology_config, self._rng)
        self.ecology.reset()
        self._relocation_done = False
        self.state = self.generator.generate(seed)
        return self.encoder.encode(self.state), {"biome_id": self.state.biome_id.value}

    def step(self, action: ActionType) -> tuple[Observation, float, bool, bool, StepInfo]:
        assert self.state is not None
        state, info = self.physiology.apply(self.state, ActionType(int(action)))
        state, info = self._apply_ecology(state, info)
        state, info = self._maybe_fixed_relocate(state, info)
        reward = self.reward_model.compute(state.body, info)
        self.state = state
        terminated = info.death_reason is not None
        truncated = state.step_idx >= self.env_config.episode_limit
        return self.encoder.encode(state), reward, terminated, truncated, info

    def render(self) -> np.ndarray:
        assert self.state is not None
        return np.array(self.state.tiles, copy=True)

    def _apply_ecology(
        self,
        state: GridWorldState,
        info: StepInfo,
    ) -> tuple[GridWorldState, StepInfo]:
        next_state, relocated = self.ecology.apply(state, self.env_config.ecology_enabled, self._continuous_mode())
        if not relocated:
            return next_state, info
        return next_state, replace(info, resource_relocated=True)

    def _maybe_fixed_relocate(
        self,
        state: GridWorldState,
        info: StepInfo,
    ) -> tuple[GridWorldState, StepInfo]:
        if not self._fixed_relocation_enabled():
            return state, info
        if self._relocation_done or state.step_idx != self.env_config.relocation_step:
            return state, info
        if self._rng.random() >= self.env_config.relocation_probability:
            return state, info
        self._relocation_done = True
        tiles = clone_tiles(state.tiles)
        moved = move_one_resource(tiles, state.biome_id, self._rng)
        if not moved:
            return state, info
        next_state = replace(state, tiles=tiles)
        return next_state, replace(info, resource_relocated=True)

    def _continuous_mode(self) -> RelocationMode:
        if not self.env_config.enable_relocation:
            return RelocationMode.DISABLED
        return self.env_config.relocation_mode

    def _fixed_relocation_enabled(self) -> bool:
        if not self.env_config.enable_relocation:
            return False
        return self.env_config.relocation_mode == RelocationMode.EPISODIC_FIXED
