"""Episode-local belief map."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from homeoorganism.domain.enums import CellType, Direction, ResourceType
from homeoorganism.domain.types import Observation, Pose, Vec2


@dataclass
class BeliefMap:
    grid_size: int = 11
    known_mask: np.ndarray = field(init=False)
    tile_ids: np.ndarray = field(init=False)
    last_seen_step: np.ndarray = field(init=False)
    visit_count: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.known_mask = np.zeros((self.grid_size, self.grid_size), dtype=bool)
        self.tile_ids = np.full((self.grid_size, self.grid_size), int(CellType.UNKNOWN), dtype=np.int16)
        self.last_seen_step = np.full((self.grid_size, self.grid_size), -1, dtype=np.int16)
        self.visit_count = np.zeros((self.grid_size, self.grid_size), dtype=np.int16)

    def update(self, obs: Observation) -> None:
        radius = obs.tiles.shape[0] // 2
        for row in range(obs.tiles.shape[0]):
            for col in range(obs.tiles.shape[1]):
                pos = self._world_from_local(obs.pose, col - radius, row - radius)
                if not self._inside(pos):
                    continue
                self.known_mask[pos.y, pos.x] = True
                self.tile_ids[pos.y, pos.x] = int(obs.tiles[row, col])
                self.last_seen_step[pos.y, pos.x] = obs.step_idx
        self.visit_count[obs.pose.y, obs.pose.x] += 1

    def get_known_resources(self, rtype: ResourceType, max_age: int) -> list[Vec2]:
        cell = CellType.FOOD if rtype == ResourceType.FOOD else CellType.WATER
        now = int(self.last_seen_step.max())
        resources = np.argwhere(self.tile_ids == int(cell))
        return [Vec2(int(x), int(y)) for y, x in resources if now - self.last_seen_step[y, x] <= max_age]

    def get_frontier_cells(self) -> list[Vec2]:
        cells: list[Vec2] = []
        for y in range(1, self.grid_size - 1):
            for x in range(1, self.grid_size - 1):
                pos = Vec2(x, y)
                if self.known_mask[y, x]:
                    continue
                if any(self._known_walkable(nei) for nei in self._neighbors(pos)):
                    cells.append(pos)
        return cells

    def is_walkable(self, pos: Vec2) -> bool:
        if not self._inside(pos):
            return False
        return self.tile_at(pos) != CellType.WALL

    def tile_at(self, pos: Vec2) -> CellType:
        if not self._inside(pos):
            return CellType.WALL
        return CellType(int(self.tile_ids[pos.y, pos.x]))

    def _world_from_local(self, pose: Pose, dx: int, dy: int) -> Vec2:
        if pose.dir == Direction.N:
            return Vec2(pose.x + dx, pose.y + dy)
        if pose.dir == Direction.E:
            return Vec2(pose.x - dy, pose.y + dx)
        if pose.dir == Direction.S:
            return Vec2(pose.x - dx, pose.y - dy)
        return Vec2(pose.x + dy, pose.y - dx)

    def _neighbors(self, pos: Vec2) -> tuple[Vec2, ...]:
        return (
            Vec2(pos.x + 1, pos.y),
            Vec2(pos.x - 1, pos.y),
            Vec2(pos.x, pos.y + 1),
            Vec2(pos.x, pos.y - 1),
        )

    def _inside(self, pos: Vec2) -> bool:
        return 0 <= pos.x < self.grid_size and 0 <= pos.y < self.grid_size

    def _known_walkable(self, pos: Vec2) -> bool:
        if not self._inside(pos) or not self.known_mask[pos.y, pos.x]:
            return False
        return self.tile_at(pos) != CellType.WALL

