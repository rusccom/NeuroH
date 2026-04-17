"""Gymnasium-compatible environment wrapper."""

from __future__ import annotations

from dataclasses import dataclass, replace

import gymnasium as gym
import numpy as np

from homeogrid.config.body_config import BodyConfig
from homeogrid.config.env_config import EnvConfig
from homeogrid.config.reward_config import RewardConfig
from homeogrid.domain.enums import ActionType, CellType
from homeogrid.domain.types import Observation, StepInfo, Vec2
from homeogrid.env.biome_templates import BIOME_TEMPLATES
from homeogrid.env.observation_encoder import ObservationEncoder
from homeogrid.env.physiology import PhysiologyModel
from homeogrid.env.reward_model import RewardModel
from homeogrid.env.world_generator import WorldGenerator
from homeogrid.env.world_state import GridWorldState, LANDMARK_POS, clone_tiles, find_cells, set_cell


@dataclass
class HomeoGridEnv(gym.Env):
    env_config: EnvConfig
    body_config: BodyConfig
    reward_config: RewardConfig

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
        self._relocation_done = False

    def reset(self, seed: int | None = None, options=None) -> tuple[Observation, dict]:
        super().reset(seed=seed)
        self._rng = np.random.default_rng(seed)
        self._relocation_done = False
        self.state = self.generator.generate(seed)
        return self.encoder.encode(self.state), {"biome_id": self.state.biome_id.value}

    def step(self, action: ActionType) -> tuple[Observation, float, bool, bool, StepInfo]:
        assert self.state is not None
        state, info = self.physiology.apply(self.state, ActionType(int(action)))
        state, info = self._maybe_relocate(state, info)
        reward = self.reward_model.compute(state.body, info)
        self.state = state
        terminated = info.death_reason is not None
        truncated = state.step_idx >= self.env_config.episode_limit
        return self.encoder.encode(state), reward, terminated, truncated, info

    def render(self) -> np.ndarray:
        assert self.state is not None
        return np.array(self.state.tiles, copy=True)

    def _maybe_relocate(
        self,
        state: GridWorldState,
        info: StepInfo,
    ) -> tuple[GridWorldState, StepInfo]:
        if not self.env_config.enable_relocation:
            return state, info
        if self._relocation_done or state.step_idx != self.env_config.relocation_step:
            return state, info
        if self._rng.random() > self.env_config.relocation_probability:
            return state, info
        self._relocation_done = True
        tiles = clone_tiles(state.tiles)
        moved = self._move_one_resource(tiles)
        if not moved:
            return state, info
        next_state = replace(state, tiles=tiles)
        return next_state, replace(info, resource_relocated=True)

    def _move_one_resource(self, tiles: np.ndarray) -> bool:
        resources = find_cells(tiles, CellType.FOOD) + find_cells(tiles, CellType.WATER)
        if not resources:
            return False
        source = resources[int(self._rng.integers(0, len(resources)))]
        cell = CellType(int(tiles[source.y, source.x]))
        biome_id = self.state.biome_id if self.state else next(iter(BIOME_TEMPLATES))
        target = self._sample_new_position(tiles, cell, biome_id)
        if target is None:
            return False
        set_cell(tiles, source, CellType.EMPTY)
        set_cell(tiles, target, cell)
        return True

    def _sample_new_position(
        self,
        tiles: np.ndarray,
        cell: CellType,
        biome_id,
    ) -> Vec2 | None:
        template = BIOME_TEMPLATES[biome_id]
        center = template.food_center if cell == CellType.FOOD else template.water_center
        candidates = [
            Vec2(center.x + dx, center.y + dy)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0))
        ]
        self._rng.shuffle(candidates)
        for pos in candidates:
            if pos in {LANDMARK_POS, Vec2(5, 6)}:
                continue
            if tiles[pos.y, pos.x] != int(CellType.EMPTY):
                continue
            return pos
        return None
