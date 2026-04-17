"""Hidden world state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from homeogrid.domain.enums import BiomeId, CellType, Direction
from homeogrid.domain.types import BodyState, Pose, Vec2


START_POSE = Pose(5, 6, Direction.N)
LANDMARK_POS = Vec2(5, 5)


@dataclass(frozen=True)
class GridWorldState:
    biome_id: BiomeId
    landmark_id: int
    tiles: np.ndarray
    pose: Pose
    body: BodyState
    step_idx: int


def clone_tiles(tiles: np.ndarray) -> np.ndarray:
    return np.array(tiles, copy=True, dtype=np.int16)


def get_cell(tiles: np.ndarray, pos: Vec2) -> CellType:
    return CellType(int(tiles[pos.y, pos.x]))


def set_cell(tiles: np.ndarray, pos: Vec2, value: CellType) -> None:
    tiles[pos.y, pos.x] = int(value)


def find_cells(tiles: np.ndarray, value: CellType) -> list[Vec2]:
    y_idx, x_idx = np.where(tiles == int(value))
    return [Vec2(int(x), int(y)) for y, x in zip(y_idx, x_idx, strict=True)]


def forward_vec(direction: Direction) -> Vec2:
    vectors = {
        Direction.N: Vec2(0, -1),
        Direction.E: Vec2(1, 0),
        Direction.S: Vec2(0, 1),
        Direction.W: Vec2(-1, 0),
    }
    return vectors[direction]


def add_vec(pos: Vec2, delta: Vec2) -> Vec2:
    return Vec2(pos.x + delta.x, pos.y + delta.y)


def clamp_body(body: BodyState, energy_max: int, water_max: int) -> BodyState:
    energy = max(0, min(energy_max, body.energy))
    water = max(0, min(water_max, body.water))
    alive = energy > 0 and water > 0
    return BodyState(energy, water, body.last_collision, alive)


def is_valid_empty(tiles: np.ndarray, pos: Vec2, blocked: Iterable[Vec2]) -> bool:
    if pos in blocked:
        return False
    if get_cell(tiles, pos) != CellType.EMPTY:
        return False
    return True
