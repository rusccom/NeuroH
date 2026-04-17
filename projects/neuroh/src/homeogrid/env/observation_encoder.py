"""Observation encoding."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from homeogrid.config.env_config import EnvConfig
from homeogrid.domain.enums import CellType, Direction
from homeogrid.domain.types import Observation, Pose, Vec2
from homeogrid.env.world_state import GridWorldState, get_cell


@dataclass
class ObservationEncoder:
    env_config: EnvConfig

    def encode(self, state: GridWorldState) -> Observation:
        radius = self.env_config.view_size // 2
        size = state.tiles.shape[0]
        tiles = self._blank_tiles()
        landmark_ids = np.zeros_like(tiles)
        for row in range(-radius, radius + 1):
            for col in range(-radius, radius + 1):
                self._encode_cell(state, tiles, landmark_ids, row, col, radius, size)
        return Observation(
            tiles=tiles,
            landmark_ids=landmark_ids,
            pose=state.pose,
            body=state.body,
            step_idx=state.step_idx,
        )

    def _blank_tiles(self) -> np.ndarray:
        return np.full((self.env_config.view_size, self.env_config.view_size), int(CellType.WALL), dtype=np.int16)

    def _encode_cell(self, state, tiles, landmark_ids, row: int, col: int, radius: int, size: int) -> None:
        world = self._to_world(state.pose, col, row)
        view_y = row + radius
        view_x = col + radius
        if not (0 <= world.x < size and 0 <= world.y < size):
            return
        cell = get_cell(state.tiles, world)
        tiles[view_y, view_x] = int(cell)
        if cell == CellType.LANDMARK:
            landmark_ids[view_y, view_x] = state.landmark_id

    def _to_world(self, pose: Pose, dx: int, dy: int) -> Vec2:
        if pose.dir == Direction.N:
            return Vec2(pose.x + dx, pose.y + dy)
        if pose.dir == Direction.E:
            return Vec2(pose.x - dy, pose.y + dx)
        if pose.dir == Direction.S:
            return Vec2(pose.x - dx, pose.y - dy)
        return Vec2(pose.x + dy, pose.y - dx)
