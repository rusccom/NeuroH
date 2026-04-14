"""Body update model."""

from __future__ import annotations

from dataclasses import dataclass, replace

from homeogrid.config.body_config import BodyConfig
from homeogrid.domain.enums import ActionType, CellType
from homeogrid.domain.types import BodyState, Pose, StepInfo, Vec2
from homeogrid.env.world_state import (
    GridWorldState,
    add_vec,
    clamp_body,
    clone_tiles,
    forward_vec,
    get_cell,
    set_cell,
)


@dataclass
class PhysiologyModel:
    body_config: BodyConfig

    def apply(self, state: GridWorldState, action: ActionType) -> tuple[GridWorldState, StepInfo]:
        tiles = clone_tiles(state.tiles)
        pose = self._next_pose(state.pose, action, tiles)
        body, info = self._next_body(state, action, pose, tiles)
        next_state = GridWorldState(
            biome_id=state.biome_id,
            landmark_id=state.landmark_id,
            tiles=tiles,
            pose=pose,
            body=body,
            step_idx=state.step_idx + 1,
        )
        return next_state, info

    def _next_pose(self, pose: Pose, action: ActionType, tiles) -> Pose:
        if action == ActionType.TURN_LEFT:
            return replace(pose, dir=pose.dir.left())
        if action == ActionType.TURN_RIGHT:
            return replace(pose, dir=pose.dir.right())
        if action != ActionType.MOVE_FORWARD:
            return pose
        target = add_vec(Vec2(pose.x, pose.y), forward_vec(pose.dir))
        if get_cell(tiles, target) == CellType.WALL:
            return pose
        return replace(pose, x=target.x, y=target.y)

    def _next_body(
        self,
        state: GridWorldState,
        action: ActionType,
        pose: Pose,
        tiles,
    ) -> tuple[BodyState, StepInfo]:
        collision = action == ActionType.MOVE_FORWARD and pose == state.pose
        entered_rough = self._entered_rough(action, pose, tiles)
        energy_cost, water_cost = self._movement_costs(state.body, action, entered_rough)
        body = BodyState(
            energy=state.body.energy - energy_cost,
            water=state.body.water - water_cost,
            last_collision=collision,
            alive=True,
        )
        body, food_used, water_used = self._apply_interact(body, pose, action, tiles)
        body = clamp_body(body, self.body_config.energy_max, self.body_config.water_max)
        reason = self._death_reason(body)
        return body, self._build_info(collision, entered_rough, food_used, water_used, energy_cost, water_cost, reason)

    def _apply_interact(self, body: BodyState, pose: Pose, action: ActionType, tiles):
        if action != ActionType.INTERACT:
            return body, False, False
        front = add_vec(Vec2(pose.x, pose.y), forward_vec(pose.dir))
        cell = get_cell(tiles, front)
        if cell == CellType.FOOD:
            set_cell(tiles, front, CellType.EMPTY)
            return replace(body, energy=body.energy + self.body_config.interact_gain), True, False
        if cell == CellType.WATER:
            set_cell(tiles, front, CellType.EMPTY)
            return replace(body, water=body.water + self.body_config.interact_gain), False, True
        return body, False, False

    def _is_low(self, body: BodyState) -> bool:
        return any(value < self.body_config.low_state_threshold for value in (body.energy, body.water))

    def _death_reason(self, body: BodyState) -> str | None:
        if body.energy <= 0:
            return "energy_depleted"
        if body.water <= 0:
            return "water_depleted"
        return None

    def _entered_rough(self, action: ActionType, pose: Pose, tiles) -> bool:
        if action != ActionType.MOVE_FORWARD:
            return False
        return get_cell(tiles, Vec2(pose.x, pose.y)) == CellType.ROUGH

    def _movement_costs(self, body: BodyState, action: ActionType, entered_rough: bool) -> tuple[int, int]:
        energy_cost = self.body_config.base_energy_cost
        water_cost = self.body_config.base_water_cost
        if action == ActionType.MOVE_FORWARD:
            energy_cost += self.body_config.move_extra_energy_cost
        if entered_rough:
            energy_cost += self.body_config.rough_extra_energy_cost
            water_cost += self.body_config.rough_extra_water_cost
        if self._is_low(body) and action == ActionType.MOVE_FORWARD:
            energy_cost += self.body_config.low_state_move_extra_energy_cost
        return energy_cost, water_cost

    def _build_info(self, collision, entered_rough, food_used, water_used, energy_cost, water_cost, reason):
        return StepInfo(
            collision=collision,
            entered_rough=entered_rough,
            consumed_food=food_used,
            consumed_water=water_used,
            action_cost_energy=energy_cost,
            action_cost_water=water_cost,
            resource_relocated=False,
            death_reason=reason,
        )
