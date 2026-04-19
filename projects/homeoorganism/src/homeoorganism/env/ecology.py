"""Continuous-life ecology layer."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from homeoorganism.config.ecology_config import EcologyConfig
from homeoorganism.config.relocation_mode import RelocationMode
from homeoorganism.domain.enums import BiomeId, CellType
from homeoorganism.domain.types import Vec2
from homeoorganism.env.biome_templates import BIOME_TEMPLATES
from homeoorganism.env.world_state import (
    GridWorldState,
    LANDMARK_POS,
    START_POSE,
    clone_tiles,
    find_cells,
    set_cell,
)


@dataclass
class EcologyLayer:
    """Regeneration uses Gaussian jitter around mean delay.

    `regen_jitter` acts as a coefficient of variation. `0.0` makes deadlines
    deterministic, which keeps edge-case tests stable.
    """

    config: EcologyConfig
    rng: np.random.Generator
    _next_food_regen_tick: int | None = None
    _next_water_regen_tick: int | None = None
    _next_relocation_tick: int = 0
    _skipped_regens: int = 0

    def reset(self, start_tick: int = 0) -> None:
        self._next_food_regen_tick = self._sample_deadline(start_tick, self.config.food_regen_mean_ticks)
        self._next_water_regen_tick = self._sample_deadline(start_tick, self.config.water_regen_mean_ticks)
        self._next_relocation_tick = start_tick + self.config.relocation_period_ticks
        self._skipped_regens = 0

    def apply(
        self,
        state: GridWorldState,
        enabled: bool,
        relocation_mode: RelocationMode,
    ) -> tuple[GridWorldState, bool]:
        tiles = clone_tiles(state.tiles)
        relocated = self._maybe_periodic_relocate(tiles, state, relocation_mode)
        if relocated:
            # Per rc4_spec section 4, regeneration is skipped on relocation ticks.
            return replace(state, tiles=tiles), True
        regenerated = enabled and self._maybe_regenerate(tiles, state)
        if not regenerated:
            return state, False
        return replace(state, tiles=tiles), False

    def _maybe_periodic_relocate(
        self,
        tiles: np.ndarray,
        state: GridWorldState,
        relocation_mode: RelocationMode,
    ) -> bool:
        if relocation_mode != RelocationMode.CONTINUOUS_PERIODIC:
            return False
        if state.step_idx < self._next_relocation_tick:
            return False
        self._next_relocation_tick = state.step_idx + self.config.relocation_period_ticks
        if self.rng.random() >= self.config.relocation_probability:
            return False
        return move_one_resource(tiles, state.biome_id, self.rng)

    def _maybe_regenerate(self, tiles: np.ndarray, state: GridWorldState) -> bool:
        food = self._maybe_regenerate_resource(tiles, state, CellType.FOOD)
        water = self._maybe_regenerate_resource(tiles, state, CellType.WATER)
        return food or water

    def _maybe_regenerate_resource(
        self,
        tiles: np.ndarray,
        state: GridWorldState,
        cell: CellType,
    ) -> bool:
        if state.step_idx < self._deadline(cell):
            return False
        placed = False
        if count_nodes(tiles, cell) < self._target_count(cell):
            placed = place_resource(tiles, cell, state.biome_id, self.rng)
            if not placed:
                self._skipped_regens += 1
        self._set_deadline(cell, self._sample_deadline(state.step_idx, self._mean_ticks(cell)))
        return placed

    def _deadline(self, cell: CellType) -> int:
        return self._next_food_regen_tick if cell == CellType.FOOD else self._next_water_regen_tick

    def _mean_ticks(self, cell: CellType) -> int:
        if cell == CellType.FOOD:
            return self.config.food_regen_mean_ticks
        return self.config.water_regen_mean_ticks

    def _sample_deadline(self, start_tick: int, mean_ticks: int) -> int:
        if self.config.regen_jitter == 0:
            delay = mean_ticks
        else:
            delay = int(self.rng.normal(mean_ticks, mean_ticks * self.config.regen_jitter))
        return start_tick + max(1, delay)

    def _set_deadline(self, cell: CellType, value: int) -> None:
        if cell == CellType.FOOD:
            self._next_food_regen_tick = value
            return
        self._next_water_regen_tick = value

    def _target_count(self, cell: CellType) -> int:
        if cell == CellType.FOOD:
            return self.config.food_target_count
        return self.config.water_target_count


def count_nodes(tiles: np.ndarray, cell: CellType) -> int:
    return len(find_cells(tiles, cell))


def move_one_resource(
    tiles: np.ndarray,
    biome_id: BiomeId,
    rng: np.random.Generator,
) -> bool:
    resources = find_cells(tiles, CellType.FOOD) + find_cells(tiles, CellType.WATER)
    if not resources:
        return False
    source = resources[int(rng.integers(0, len(resources)))]
    cell = CellType(int(tiles[source.y, source.x]))
    target = sample_resource_target(tiles, cell, biome_id, rng)
    if target is None:
        return False
    set_cell(tiles, source, CellType.EMPTY)
    set_cell(tiles, target, cell)
    return True


def place_resource(
    tiles: np.ndarray,
    cell: CellType,
    biome_id: BiomeId,
    rng: np.random.Generator,
) -> bool:
    target = sample_resource_target(tiles, cell, biome_id, rng)
    if target is None:
        return False
    set_cell(tiles, target, cell)
    return True


def sample_resource_target(
    tiles: np.ndarray,
    cell: CellType,
    biome_id: BiomeId,
    rng: np.random.Generator,
) -> Vec2 | None:
    for pos in candidate_cells(cell, biome_id, rng):
        if pos in {LANDMARK_POS, Vec2(START_POSE.x, START_POSE.y)}:
            continue
        if tiles[pos.y, pos.x] != int(CellType.EMPTY):
            continue
        return pos
    return None


def candidate_cells(
    cell: CellType,
    biome_id: BiomeId,
    rng: np.random.Generator,
) -> list[Vec2]:
    template = BIOME_TEMPLATES[biome_id]
    center = template.food_center if cell == CellType.FOOD else template.water_center
    candidates = [
        Vec2(center.x + dx, center.y + dy)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0))
    ]
    rng.shuffle(candidates)
    return candidates
