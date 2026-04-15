"""Metrics collection."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from homeogrid.domain.enums import EventType, ResourceType, TargetSource
from homeogrid.domain.types import EpisodeSummary, Observation, SalientEvent, Transition


@dataclass
class MetricsCollector:
    total_reward: float = 0.0
    survival_steps: int = 0
    collision_count: int = 0
    source_counts: dict[str, int] = field(default_factory=dict)
    steps_to_first_food: int | None = None
    steps_to_first_water: int | None = None
    return_steps_to_seen_food: int | None = None
    return_steps_to_seen_water: int | None = None
    steps_to_first_needed_resource: int | None = None
    return_steps_to_seen_resource: int | None = None
    mean_energy_deficit: float = 0.0
    mean_water_deficit: float = 0.0
    need_switch_count: int = 0
    stuck_windows: int = 0
    relocation_recovery_steps: int | None = None
    relocation_recovery_success_rate: int = 0
    action_history: deque[str] = field(default_factory=lambda: deque(maxlen=64))
    pose_history: deque[tuple[int, int]] = field(default_factory=lambda: deque(maxlen=64))
    _relocation_step: int | None = None

    def begin_episode(self, obs: Observation) -> None:
        self._reset_episode_state()
        self.action_history.clear()
        self.pose_history.clear()
        self.pose_history.append((obs.pose.x, obs.pose.y))
        self.source_counts = self._empty_source_counts()

    def on_step(
        self,
        transition: Transition,
        selected_source,
        events: list[SalientEvent] | None = None,
    ) -> None:
        self.total_reward += transition.reward
        self.survival_steps += 1
        self._track_collision(transition)
        self.pose_history.append((transition.next_obs.pose.x, transition.next_obs.pose.y))
        self.action_history.append(transition.action.name)
        active_need = self._active_need(transition.prev_obs)
        self._track_resource_timings(transition, selected_source, active_need)
        self._track_means(transition)
        self._track_source(selected_source)
        self._track_need_switch(events or [])
        self._track_stuck()

    def end_episode(self, summary: EpisodeSummary) -> dict:
        steps = max(summary.steps, 1)
        row = self._summary_fields(summary)
        row.update(self._mean_fields(steps))
        row.update(self._source_fields())
        return row

    def _mean_fields(self, steps: int) -> dict:
        return {
            "mean_energy_deficit": self.mean_energy_deficit / steps,
            "mean_water_deficit": self.mean_water_deficit / steps,
            "need_switch_count": self.need_switch_count,
            "stuck_windows": self.stuck_windows,
            "relocation_recovery_steps": self.relocation_recovery_steps,
            "relocation_recovery_success_rate": self.relocation_recovery_success_rate,
        }

    def _summary_fields(self, summary: EpisodeSummary) -> dict:
        return {
            "episode_id": summary.episode_id,
            "biome_id": summary.biome_id.value if summary.biome_id else None,
            "steps": summary.steps,
            "total_reward": summary.total_reward,
            "died": summary.died,
            "death_reason": summary.death_reason,
            "survival_steps": self.survival_steps,
            "collision_count": self.collision_count,
            "steps_to_first_food": self.steps_to_first_food,
            "steps_to_first_water": self.steps_to_first_water,
            "return_steps_to_seen_food": self.return_steps_to_seen_food,
            "return_steps_to_seen_water": self.return_steps_to_seen_water,
            "steps_to_first_needed_resource": self.steps_to_first_needed_resource,
            "return_steps_to_seen_resource": self.return_steps_to_seen_resource,
        }

    def collision_rate_window(self) -> float:
        if not self.action_history:
            return 0.0
        return min(1.0, self.collision_count / max(1, len(self.action_history)))

    def action_switch_rate_window(self) -> float:
        if len(self.action_history) < 2:
            return 0.0
        switches = sum(1 for prev, cur in zip(self.action_history, list(self.action_history)[1:]) if prev != cur)
        return min(1.0, switches / max(1, len(self.action_history) - 1))

    def stuck_window(self) -> bool:
        if len(self.pose_history) < 12:
            return False
        return len(set(self.pose_history)) <= 2

    def _reset_episode_state(self) -> None:
        self.total_reward = 0.0
        self.survival_steps = 0
        self.collision_count = 0
        self.steps_to_first_food = None
        self.steps_to_first_water = None
        self.return_steps_to_seen_food = None
        self.return_steps_to_seen_water = None
        self.steps_to_first_needed_resource = None
        self.return_steps_to_seen_resource = None
        self.mean_energy_deficit = 0.0
        self.mean_water_deficit = 0.0
        self.need_switch_count = 0
        self.stuck_windows = 0
        self.relocation_recovery_steps = None
        self.relocation_recovery_success_rate = 0
        self._relocation_step = None

    def _empty_source_counts(self) -> dict[str, int]:
        return {name.value: 0 for name in TargetSource}

    def _track_collision(self, transition: Transition) -> None:
        if transition.info.collision:
            self.collision_count += 1

    def _track_resource_timings(
        self,
        transition: Transition,
        selected_source,
        active_need: ResourceType | None,
    ) -> None:
        if transition.info.resource_relocated and self._relocation_step is None:
            self._relocation_step = transition.next_obs.step_idx
        consumed = self._consumed_resource(transition)
        if consumed is None:
            return
        step_idx = transition.next_obs.step_idx
        self._track_first_resource(consumed, step_idx)
        self._track_fast_return(consumed, step_idx, selected_source)
        if consumed == active_need and self.steps_to_first_needed_resource is None:
            self.steps_to_first_needed_resource = step_idx
        self._track_relocation_recovery(step_idx)

    def _track_means(self, transition: Transition) -> None:
        energy_gap = max(0, 70 - transition.next_obs.body.energy) / 70
        water_gap = max(0, 70 - transition.next_obs.body.water) / 70
        self.mean_energy_deficit += energy_gap
        self.mean_water_deficit += water_gap

    def _track_need_switch(self, events: list[SalientEvent]) -> None:
        self.need_switch_count += sum(1 for event in events if event.event_type == EventType.NEED_SWITCH)

    def _track_stuck(self) -> None:
        if self.stuck_window():
            self.stuck_windows += 1

    def _track_source(self, selected_source) -> None:
        if selected_source is None:
            return
        key = selected_source.value if hasattr(selected_source, "value") else str(selected_source)
        self.source_counts[key] += 1

    def _source_fields(self) -> dict:
        total = max(1, sum(self.source_counts.values()))
        return {
            "source_fast": self.source_counts[TargetSource.FAST.value],
            "source_slow": self.source_counts[TargetSource.SLOW.value],
            "source_explore": self.source_counts[TargetSource.EXPLORE.value],
            "source_fast_share": self.source_counts[TargetSource.FAST.value] / total,
            "source_slow_share": self.source_counts[TargetSource.SLOW.value] / total,
            "source_explore_share": self.source_counts[TargetSource.EXPLORE.value] / total,
        }

    def _track_first_resource(self, consumed: ResourceType, step_idx: int) -> None:
        if consumed == ResourceType.FOOD and self.steps_to_first_food is None:
            self.steps_to_first_food = step_idx
        if consumed == ResourceType.WATER and self.steps_to_first_water is None:
            self.steps_to_first_water = step_idx

    def _track_fast_return(self, consumed: ResourceType, step_idx: int, selected_source) -> None:
        if selected_source != TargetSource.FAST:
            return
        if self.return_steps_to_seen_resource is None:
            self.return_steps_to_seen_resource = step_idx
        if consumed == ResourceType.FOOD and self.return_steps_to_seen_food is None:
            self.return_steps_to_seen_food = step_idx
        if consumed == ResourceType.WATER and self.return_steps_to_seen_water is None:
            self.return_steps_to_seen_water = step_idx

    def _track_relocation_recovery(self, step_idx: int) -> None:
        if self._relocation_step is None or self.relocation_recovery_steps is not None:
            return
        self.relocation_recovery_steps = step_idx - self._relocation_step
        self.relocation_recovery_success_rate = 1
        self._relocation_step = None

    def _consumed_resource(self, transition: Transition) -> ResourceType | None:
        if transition.info.consumed_food:
            return ResourceType.FOOD
        if transition.info.consumed_water:
            return ResourceType.WATER
        return None

    def _active_need(self, obs: Observation) -> ResourceType | None:
        energy_deficit = max(0, 70 - obs.body.energy) / 70
        water_deficit = max(0, 70 - obs.body.water) / 70
        if max(energy_deficit, water_deficit) < 0.1:
            return None
        return ResourceType.FOOD if energy_deficit > water_deficit else ResourceType.WATER
