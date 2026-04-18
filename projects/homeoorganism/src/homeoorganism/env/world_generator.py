"""World generation logic."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from homeoorganism.config.body_config import BodyConfig
from homeoorganism.config.env_config import EnvConfig
from homeoorganism.domain.enums import BiomeId, CellType
from homeoorganism.domain.types import BodyState, Vec2
from homeoorganism.env.biome_templates import BIOME_TEMPLATES, BiomeTemplate
from homeoorganism.env.world_state import GridWorldState, LANDMARK_POS, START_POSE, set_cell


@dataclass
class WorldGenerator:
    env_config: EnvConfig
    body_config: BodyConfig

    def generate(self, seed: int | None = None) -> GridWorldState:
        rng = np.random.default_rng(seed)
        biome = self._pick_biome(rng)
        tiles = self._build_empty_world()
        set_cell(tiles, LANDMARK_POS, CellType.LANDMARK)
        self._place_resources(tiles, biome, rng)
        self._place_rough(tiles, biome, rng)
        return GridWorldState(
            biome_id=biome.biome_id,
            landmark_id=biome.landmark_id,
            tiles=tiles,
            pose=START_POSE,
            body=self._initial_body(),
            step_idx=0,
        )

    def _pick_biome(self, rng: np.random.Generator) -> BiomeTemplate:
        biomes = list(BiomeId)
        biome = biomes[int(rng.integers(0, len(biomes)))]
        return BIOME_TEMPLATES[biome]

    def _build_empty_world(self) -> np.ndarray:
        size = self.env_config.grid_size
        tiles = np.full((size, size), int(CellType.EMPTY), dtype=np.int16)
        tiles[0, :] = int(CellType.WALL)
        tiles[-1, :] = int(CellType.WALL)
        tiles[:, 0] = int(CellType.WALL)
        tiles[:, -1] = int(CellType.WALL)
        return tiles

    def _place_resources(
        self,
        tiles: np.ndarray,
        biome: BiomeTemplate,
        rng: np.random.Generator,
    ) -> None:
        blocked = self._blocked_cells()
        self._place_near_center(
            tiles,
            biome.food_center,
            CellType.FOOD,
            self.env_config.food_nodes_per_episode,
            blocked,
            rng,
        )
        self._place_near_center(
            tiles,
            biome.water_center,
            CellType.WATER,
            self.env_config.water_nodes_per_episode,
            blocked,
            rng,
        )

    def _initial_body(self) -> BodyState:
        return BodyState(self.body_config.energy_start, self.body_config.water_start, False, True)

    def _blocked_cells(self) -> set[Vec2]:
        return {LANDMARK_POS, Vec2(START_POSE.x, START_POSE.y)}

    def _place_rough(
        self,
        tiles: np.ndarray,
        biome: BiomeTemplate,
        rng: np.random.Generator,
    ) -> None:
        blocked = {LANDMARK_POS, Vec2(START_POSE.x, START_POSE.y)}
        for center in biome.rough_centers[: self.env_config.rough_patches_per_episode]:
            for pos in self._candidate_positions(center, rng):
                if pos in blocked:
                    continue
                if tiles[pos.y, pos.x] != int(CellType.EMPTY):
                    continue
                set_cell(tiles, pos, CellType.ROUGH)
                break

    def _place_near_center(
        self,
        tiles: np.ndarray,
        center: Vec2,
        value: CellType,
        count: int,
        blocked: set[Vec2],
        rng: np.random.Generator,
    ) -> None:
        placed = 0
        candidates = self._candidate_positions(center, rng)
        while candidates and placed < count:
            pos = candidates.pop(0)
            if pos in blocked:
                continue
            if tiles[pos.y, pos.x] != int(CellType.EMPTY):
                continue
            set_cell(tiles, pos, value)
            blocked.add(pos)
            placed += 1

    def _candidate_positions(
        self,
        center: Vec2,
        rng: np.random.Generator,
    ) -> list[Vec2]:
        offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(offsets)
        return [Vec2(center.x + dx, center.y + dy) for dx, dy in offsets]
