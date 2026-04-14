"""Low-level action selection from a plan."""

from dataclasses import dataclass

from homeogrid.domain.enums import ActionType, Direction
from homeogrid.domain.types import Plan, Pose, TargetProposal


@dataclass
class LowLevelController:
    def next_action(self, pose: Pose, proposal: TargetProposal, plan: Plan) -> ActionType:
        if proposal.stance_pose and pose.x == proposal.stance_pose.x and pose.y == proposal.stance_pose.y:
            return self._stance_action(pose.dir, proposal.stance_pose.dir)
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

    def _desired_dir(self, pose: Pose, next_pose: Pose) -> Direction:
        if next_pose.x > pose.x:
            return Direction.E
        if next_pose.x < pose.x:
            return Direction.W
        if next_pose.y > pose.y:
            return Direction.S
        return Direction.N

    def _turn_towards(self, current: Direction, desired: Direction) -> ActionType:
        if (int(desired) - int(current)) % 4 == 1:
            return ActionType.TURN_RIGHT
        return ActionType.TURN_LEFT
