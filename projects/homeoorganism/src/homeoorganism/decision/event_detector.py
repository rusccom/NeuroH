"""Step-level event detection."""

from __future__ import annotations

from dataclasses import dataclass

from homeoorganism.agent.belief_map import BeliefMap
from homeoorganism.domain.enums import CellType, Direction, EventType, ResourceType
from homeoorganism.domain.events import EVENT_SALIENCE
from homeoorganism.domain.types import NeedState, Pose, SalientEvent, Transition, Vec2


@dataclass
class EventDetector:
    def detect(
        self,
        transition: Transition,
        prev_need: NeedState | None,
        next_need: NeedState | None,
        biome_id,
        belief_map: BeliefMap,
    ) -> list[SalientEvent]:
        events = self._resource_events(transition, biome_id)
        if transition.info.collision:
            events.append(self._plain_event(EventType.COLLISION, transition, biome_id))
        if transition.info.death_reason:
            events.append(self._plain_event(EventType.DEATH, transition, biome_id))
        if transition.info.resource_relocated:
            events.append(self._plain_event(EventType.RESOURCE_RELOCATED, transition, biome_id))
        if self._need_switched(prev_need, next_need):
            events.append(self._plain_event(EventType.NEED_SWITCH, transition, biome_id))
        if transition.next_obs.landmark_ids.max() > 0 and biome_id is not None:
            events.append(self._plain_event(EventType.BIOME_IDENTIFIED, transition, biome_id))
        return events

    def _resource_events(self, transition: Transition, biome_id) -> list[SalientEvent]:
        events = []
        if transition.info.consumed_food:
            events.append(self._typed_event(EventType.RESOURCE_CONSUMED, ResourceType.FOOD, transition, biome_id))
        if transition.info.consumed_water:
            events.append(self._typed_event(EventType.RESOURCE_CONSUMED, ResourceType.WATER, transition, biome_id))
        for pos, rtype in visible_resources(transition.next_obs):
            events.append(
                SalientEvent(
                    event_type=EventType.RESOURCE_OBSERVED,
                    step_idx=transition.next_obs.step_idx,
                    biome_id=biome_id,
                    pose=transition.next_obs.pose,
                    resource_type=rtype,
                    action=transition.action,
                    salience=EVENT_SALIENCE[EventType.RESOURCE_OBSERVED],
                    position=pos,
                )
            )
        return events

    def _plain_event(self, event_type, transition, biome_id) -> SalientEvent:
        return SalientEvent(
            event_type=event_type,
            step_idx=transition.next_obs.step_idx,
            biome_id=biome_id,
            pose=transition.next_obs.pose,
            resource_type=None,
            action=transition.action,
            salience=EVENT_SALIENCE[event_type],
            position=None,
        )

    def _typed_event(self, event_type, rtype, transition, biome_id) -> SalientEvent:
        return SalientEvent(
            event_type=event_type,
            step_idx=transition.next_obs.step_idx,
            biome_id=biome_id,
            pose=transition.next_obs.pose,
            resource_type=rtype,
            action=transition.action,
            salience=EVENT_SALIENCE[event_type],
            position=None,
        )

    def _need_switched(self, prev_need: NeedState | None, next_need: NeedState | None) -> bool:
        if prev_need is None or next_need is None:
            return False
        return prev_need.active_need != next_need.active_need


def belief_like_transform(pose: Pose, dx: int, dy: int) -> Vec2:
    if pose.dir == Direction.N:
        return Vec2(pose.x + dx, pose.y + dy)
    if pose.dir == Direction.E:
        return Vec2(pose.x - dy, pose.y + dx)
    if pose.dir == Direction.S:
        return Vec2(pose.x - dx, pose.y - dy)
    return Vec2(pose.x + dy, pose.y - dx)


def visible_resources(obs) -> list[tuple[Vec2, ResourceType]]:
    found = []
    radius = obs.tiles.shape[0] // 2
    for row in range(obs.tiles.shape[0]):
        for col in range(obs.tiles.shape[1]):
            tile = CellType(int(obs.tiles[row, col]))
            if tile not in {CellType.FOOD, CellType.WATER}:
                continue
            pos = belief_like_transform(obs.pose, col - radius, row - radius)
            rtype = ResourceType.FOOD if tile == CellType.FOOD else ResourceType.WATER
            found.append((pos, rtype))
    return found

