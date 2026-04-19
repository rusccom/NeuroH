"""Low-level action selection from a plan."""

from dataclasses import dataclass

from homeoorganism.domain.enums import ActionType, Direction, ExecutionMode
from homeoorganism.domain.types import Plan, Pose, TargetProposal, Vec2


@dataclass
class LowLevelController:
    def next_action(self, pose: Pose, proposal: TargetProposal, plan: Plan) -> ActionType:
        stance_dir = self._stance_dir(pose, proposal)
        if stance_dir is not None:
            return self._stance_action(pose.dir, stance_dir)
        if not plan.valid:
            return ActionType.WAIT
        if not plan.waypoints:
            return self._final_turn(pose, plan)
        desired = self._desired_dir(pose, plan.waypoints[0])
        if desired != pose.dir:
            return self._turn_towards(pose.dir, desired)
        return ActionType.MOVE_FORWARD

    def _stance_action(self, current: Direction, expected: Direction | None) -> ActionType:
        if expected is None or current == expected:
            return ActionType.INTERACT
        return self._turn_towards(current, expected)

    def _final_turn(self, pose: Pose, plan: Plan) -> ActionType:
        if plan.final_dir is None or pose.dir == plan.final_dir:
            return ActionType.WAIT
        return self._turn_towards(pose.dir, plan.final_dir)

    def _stance_dir(self, pose: Pose, proposal: TargetProposal) -> Direction | None:
        if proposal.stance_pose and self._same_cell(pose, proposal.stance_pose):
            return proposal.stance_pose.dir
        if (
            proposal.execution_mode != ExecutionMode.DIRECT
            or proposal.exact_cell is None
            or proposal.resource_type is None
        ):
            return None
        if not self._adjacent(pose, proposal.exact_cell):
            return None
        return self._desired_dir(pose, Pose(proposal.exact_cell.x, proposal.exact_cell.y, pose.dir))

    def _desired_dir(self, pose: Pose, next_pose: Pose) -> Direction:
        if next_pose.x > pose.x:
            return Direction.E
        if next_pose.x < pose.x:
            return Direction.W
        if next_pose.y > pose.y:
            return Direction.S
        return Direction.N

    def _adjacent(self, pose: Pose, target: Vec2) -> bool:
        return abs(target.x - pose.x) + abs(target.y - pose.y) == 1

    def _same_cell(self, pose: Pose, other: Pose) -> bool:
        return pose.x == other.x and pose.y == other.y

    def _turn_towards(self, current: Direction, desired: Direction) -> ActionType:
        if (int(desired) - int(current)) % 4 == 1:
            return ActionType.TURN_RIGHT
        return ActionType.TURN_LEFT

