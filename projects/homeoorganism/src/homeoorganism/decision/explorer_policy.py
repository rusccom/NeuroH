"""Exploration proposals."""

from dataclasses import dataclass, replace

from homeoorganism.agent.belief_map import BeliefMap
from homeoorganism.domain.enums import ExecutionMode, TargetSource
from homeoorganism.domain.types import Pose, TargetProposal, Vec2


@dataclass
class ExplorerPolicy:
    def propose_global(self, belief_map: BeliefMap, pose: Pose) -> TargetProposal:
        frontier = belief_map.get_frontier_cells()
        return self._best_frontier(frontier, pose)

    def propose_in_region(
        self,
        belief_map: BeliefMap,
        pose: Pose,
        region_cells: list[Vec2],
    ) -> TargetProposal:
        frontier = [cell for cell in belief_map.get_frontier_cells() if cell in region_cells]
        if frontier:
            proposal = self._best_frontier(frontier, pose)
            return replace(proposal, execution_mode=ExecutionMode.REGIONAL_EXPLORE)
        return self.propose_global(belief_map, pose)

    def _best_frontier(self, frontier: list[Vec2], pose: Pose) -> TargetProposal:
        if not frontier:
            return TargetProposal(
                TargetSource.EXPLORE,
                None,
                0.0,
                exact_cell=Vec2(pose.x, pose.y),
                execution_mode=ExecutionMode.GLOBAL_EXPLORE,
            )
        best = min(frontier, key=lambda pos: abs(pos.x - pose.x) + abs(pos.y - pose.y))
        return TargetProposal(
            TargetSource.EXPLORE,
            None,
            0.4,
            exact_cell=best,
            execution_mode=ExecutionMode.GLOBAL_EXPLORE,
        )

