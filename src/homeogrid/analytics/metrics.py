"""Metrics collection."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from homeogrid.domain.enums import TargetSource
from homeogrid.domain.types import EpisodeSummary, Observation, Transition


@dataclass
class MetricsCollector:
    total_reward: float = 0.0
    survival_steps: int = 0
    collision_count: int = 0
    source_counts: dict[str, int] = field(default_factory=lambda: {name: 0 for name in TargetSource})
    steps_to_first_food: int | None = None
    steps_to_first_water: int | None = None
    return_steps_to_seen_food: int | None = None
    return_steps_to_seen_water: int | None = None
    mean_energy_deficit: float = 0.0
    mean_water_deficit: float = 0.0
    need_switch_count: int = 0
    stuck_windows: int = 0
    relocation_recovery_steps: int | None = None
    action_history: deque[str] = field(default_factory=lambda: deque(maxlen=64))
    pose_history: deque[tuple[int, int]] = field(default_factory=lambda: deque(maxlen=64))

    def begin_episode(self, obs: Observation) -> None:
        self.total_reward = 0.0
        self.survival_steps = 0
        self.collision_count = 0
        self.steps_to_first_food = None
        self.steps_to_first_water = None
        self.return_steps_to_seen_food = None
        self.return_steps_to_seen_water = None
        self.mean_energy_deficit = 0.0
        self.mean_water_deficit = 0.0
        self.need_switch_count = 0
        self.stuck_windows = 0
        self.relocation_recovery_steps = None
        self.action_history.clear()
        self.pose_history.clear()
        self.pose_history.append((obs.pose.x, obs.pose.y))
        self.source_counts = {name.value: 0 for name in TargetSource}

    def on_step(self, transition: Transition, selected_source) -> None:
        self.total_reward += transition.reward
        self.survival_steps += 1
        if transition.info.collision:
            self.collision_count += 1
        self.pose_history.append((transition.next_obs.pose.x, transition.next_obs.pose.y))
        self.action_history.append(transition.action.name)
        self._track_resource_timings(transition)
        self._track_means(transition)
        self._track_source(selected_source)

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

    def _track_resource_timings(self, transition: Transition) -> None:
        if transition.info.consumed_food and self.steps_to_first_food is None:
            self.steps_to_first_food = transition.next_obs.step_idx
        if transition.info.consumed_water and self.steps_to_first_water is None:
            self.steps_to_first_water = transition.next_obs.step_idx

    def _track_means(self, transition: Transition) -> None:
        energy_gap = max(0, 70 - transition.next_obs.body.energy) / 70
        water_gap = max(0, 70 - transition.next_obs.body.water) / 70
        self.mean_energy_deficit += energy_gap
        self.mean_water_deficit += water_gap

    def _track_source(self, selected_source) -> None:
        if selected_source is None:
            return
        key = selected_source.value if hasattr(selected_source, "value") else str(selected_source)
        self.source_counts[key] += 1

    def _source_fields(self) -> dict:
        return {
            "source_fast": self.source_counts[TargetSource.FAST.value],
            "source_slow": self.source_counts[TargetSource.SLOW.value],
            "source_explore": self.source_counts[TargetSource.EXPLORE.value],
        }
