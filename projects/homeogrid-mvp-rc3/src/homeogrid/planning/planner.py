"""Grid planner."""

from __future__ import annotations

from dataclasses import dataclass, replace
from heapq import heappop, heappush

from homeogrid.agent.belief_map import BeliefMap
from homeogrid.config.planner_config import PlannerConfig
from homeogrid.domain.enums import CellType, Direction, ExecutionMode
from homeogrid.domain.types import Plan, Pose, TargetProposal, Vec2


@dataclass
class Planner:
    planner_config: PlannerConfig

    def prepare_proposal(self, belief_map: BeliefMap, pose: Pose, proposal: TargetProposal) -> TargetProposal:
        if proposal.stance_pose is not None or not self._needs_stance(proposal):
            return proposal
        stance = self._stance_for_resource(belief_map, proposal.exact_cell, pose)
        if stance is None:
            return proposal
        return replace(proposal, stance_pose=stance)

    def plan(self, belief_map: BeliefMap, pose: Pose, proposal: TargetProposal) -> Plan:
        target_pose = self._target_pose(belief_map, pose, proposal)
        if target_pose is None:
            return Plan(valid=False)
        path, cost = self._a_star(belief_map, pose, target_pose)
        if not path:
            return Plan(valid=False)
        waypoints = tuple(Pose(cell.x, cell.y, pose.dir) for cell in path[1:])
        return Plan(True, waypoints, target_pose.dir, cost)

    def _target_pose(
        self,
        belief_map: BeliefMap,
        pose: Pose,
        proposal: TargetProposal,
    ) -> Pose | None:
        if proposal.stance_pose is not None:
            return proposal.stance_pose
        if self._needs_stance(proposal):
            return self._stance_for_resource(belief_map, proposal.exact_cell, pose)
        if proposal.exact_cell:
            return Pose(proposal.exact_cell.x, proposal.exact_cell.y, pose.dir)
        if proposal.region_cells:
            cell = min(proposal.region_cells, key=lambda item: abs(item.x - pose.x) + abs(item.y - pose.y))
            return Pose(cell.x, cell.y, pose.dir)
        return None

    def _needs_stance(self, proposal: TargetProposal) -> bool:
        return (
            proposal.exact_cell is not None
            and proposal.resource_type is not None
            and proposal.execution_mode == ExecutionMode.DIRECT
        )

    def _stance_for_resource(self, belief_map: BeliefMap, cell: Vec2, pose: Pose) -> Pose | None:
        options = [
            (Vec2(cell.x, cell.y + 1), Direction.N),
            (Vec2(cell.x - 1, cell.y), Direction.E),
            (Vec2(cell.x, cell.y - 1), Direction.S),
            (Vec2(cell.x + 1, cell.y), Direction.W),
        ]
        candidates = [Pose(pos.x, pos.y, facing) for pos, facing in options if belief_map.is_walkable(pos)]
        if not candidates:
            return None
        return min(candidates, key=lambda item: abs(item.x - pose.x) + abs(item.y - pose.y))

    def _a_star(self, belief_map: BeliefMap, start: Pose, goal: Pose) -> tuple[list[Vec2], float]:
        start_cell = Vec2(start.x, start.y)
        goal_cell = Vec2(goal.x, goal.y)
        frontier = [(0.0, start_cell.x, start_cell.y, start_cell)]
        came_from: dict[Vec2, Vec2 | None] = {start_cell: None}
        costs = {start_cell: 0.0}
        while frontier:
            _, _, _, current = heappop(frontier)
            if current == goal_cell:
                return self._reconstruct(came_from, goal_cell), costs[current]
            for neighbor, step_cost in self._neighbors(belief_map, current):
                new_cost = costs[current] + step_cost
                if neighbor in costs and new_cost >= costs[neighbor]:
                    continue
                costs[neighbor] = new_cost
                came_from[neighbor] = current
                priority = new_cost + self._manhattan(neighbor, goal_cell)
                heappush(frontier, (priority, neighbor.x, neighbor.y, neighbor))
        return [], 0.0

    def _neighbors(self, belief_map: BeliefMap, pos: Vec2) -> list[tuple[Vec2, float]]:
        result = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = Vec2(pos.x + dx, pos.y + dy)
            tile = belief_map.tile_at(nxt)
            if tile == CellType.WALL:
                continue
            result.append((nxt, self._cell_cost(tile)))
        return result

    def _cell_cost(self, tile: CellType) -> float:
        if tile == CellType.ROUGH:
            return self.planner_config.rough_cost
        if tile == CellType.UNKNOWN:
            return self.planner_config.unknown_cost
        return 1.0

    def _reconstruct(self, came_from: dict[Vec2, Vec2 | None], goal: Vec2) -> list[Vec2]:
        path = [goal]
        current = goal
        while came_from[current] is not None:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path[: self.planner_config.max_plan_len]

    def _manhattan(self, left: Vec2, right: Vec2) -> int:
        return abs(left.x - right.x) + abs(left.y - right.y)
