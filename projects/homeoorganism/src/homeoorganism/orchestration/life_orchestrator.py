"""Continuous life-series orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from time import time_ns

import numpy as np

from homeoorganism.analytics.windowed_metrics import ContinuousMetrics
from homeoorganism.config.experiment_config import ExperimentConfig
from homeoorganism.config.relocation_mode import RelocationMode
from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.types import EpisodeSummary
from homeoorganism.domain.types import Transition
from homeoorganism.env.gym_env import HomeoGridEnv
from homeoorganism.monitoring.domain.enums import RunState
from homeoorganism.orchestration.life_artifacts import LifeArtifactsWriter
from homeoorganism.orchestration.life_state_store import LifeRuntime
from homeoorganism.orchestration.run_report import RunReport
from homeoorganism.orchestration.run_state_store import RunStateStore
from homeoorganism.v1_baseline.agent.core import AgentCore


@dataclass
class LifeOrchestrator:
    env: HomeoGridEnv
    agent: AgentCore
    metrics: ContinuousMetrics
    artifacts: LifeArtifactsWriter
    experiment_config: ExperimentConfig
    config_hash: str
    run_state_store: RunStateStore | None = None

    def __post_init__(self) -> None:
        self._base_env_config = self.env.env_config
        self._full_planner_config = self.agent.planner.planner_config
        self._active_mode = "continuous_full"
        self._active_seed = self.experiment_config.base_seed

    def run(
        self,
        mode: str,
        life_count: int | None = None,
        life_max_ticks: int = 5000,
    ) -> RunReport:
        requested = self._life_count(life_count)
        started_at = _current_ms()
        self._prepare_run(mode, life_max_ticks)
        life_states = tuple(self._run_life(life_id, life_max_ticks) for life_id in range(1, requested + 1))
        self._finalize_run(mode, requested, life_max_ticks, started_at, life_states)
        return self._build_report(mode, requested, life_states)

    def save_snapshot(self) -> None:
        return None

    def _prepare_run(self, mode: str, life_max_ticks: int) -> None:
        self._activate_mode(mode, life_max_ticks)
        self._reset_metrics()
        self._reset_slow_memory()
        self._set_state(RunState.RUNNING)

    def _run_life(self, life_id: int, life_max_ticks: int):
        runtime = LifeRuntime.start(life_id)
        obs = self._begin_life(life_id)
        while not self._should_finish(obs, runtime.tick, life_max_ticks):
            obs = self._step_life(runtime, obs)
        return self._complete_life(runtime, obs, life_max_ticks)

    def _begin_life(self, life_id: int):
        self._set_life(life_id)
        self.metrics.begin_life(life_id)
        obs, _ = self.env.reset(seed=self._life_seed(life_id))
        self.agent.begin_episode(obs)
        return obs

    def _step_life(self, runtime: LifeRuntime, obs):
        action = self.agent.act(obs)
        next_obs, reward, terminated, truncated, info = self.env.step(action)
        transition = Transition(obs, action, next_obs, reward, terminated, truncated, info)
        self.agent.observe_transition(transition)
        runtime.advance(next_obs.step_idx)
        self._write_tick_rows(runtime.tick, next_obs.body, info)
        return next_obs

    def _write_tick_rows(self, tick: int, body, info) -> None:
        selected = self.agent.working_buffer.state.selected_proposal
        anchor_events = self._anchor_events()
        window_rows, event_rows = self.metrics.on_tick(
            tick=tick,
            body=body,
            proposal=selected,
            consumed_resource=self._consumed_resource(info),
            anchor_events=anchor_events,
        )
        self.artifacts.append_window_rows(window_rows)
        self.artifacts.append_event_rows(event_rows)

    def _complete_life(self, runtime: LifeRuntime, obs, life_max_ticks: int):
        end_reason = self._end_reason(obs, runtime.tick, life_max_ticks)
        life_state = runtime.finalize(end_reason)
        self.agent.end_episode(self._episode_summary(life_state, obs))
        summary, event_rows, series_row = self.metrics.on_life_end(life_state.tick, end_reason)
        self.artifacts.write_life_summary(summary)
        self.artifacts.append_event_rows(event_rows)
        self.artifacts.append_series_row(series_row)
        return life_state

    def _activate_mode(self, mode: str, life_max_ticks: int) -> None:
        self._ensure_mode(mode)
        self._active_mode = mode
        self.agent.fast_memory.enabled = True
        self.agent.slow_memory.enabled = True
        self.agent.drive_model.enabled = True
        self.agent.planner.planner_config = self._full_planner_config
        self.env.env_config = replace(
            self._base_env_config,
            episode_limit=life_max_ticks,
            ecology_enabled=mode != "continuous_no_regen",
            enable_relocation=True,
            relocation_mode=RelocationMode.CONTINUOUS_PERIODIC,
        )

    def _reset_slow_memory(self) -> None:
        self.agent.slow_memory.heatmaps.fill(0.0)
        self.agent.slow_memory.episode_count = 0

    def _reset_metrics(self) -> None:
        self.metrics = ContinuousMetrics(self.metrics.window_sizes, self.metrics.block_size)

    def _finalize_run(
        self,
        mode: str,
        requested: int,
        life_max_ticks: int,
        started_at: int,
        life_states: tuple,
    ) -> None:
        self.agent.slow_memory.save(str(self.artifacts.slow_memory_path))
        self.artifacts.write_json(
            self.artifacts.manifest_path,
            self._manifest(mode, requested, life_max_ticks, started_at, life_states),
        )
        self._set_state(RunState.ENDED)

    def _manifest(self, mode: str, requested: int, life_max_ticks: int, started_at: int, life_states: tuple) -> dict:
        return {
            "run_id": self.experiment_config.run_id,
            "config_hash": self.config_hash,
            "mode": mode,
            "seed": self._active_seed,
            "requested_lives": requested,
            "completed_lives": len(life_states),
            "life_max_ticks": life_max_ticks,
            "started_at_ts_ms": started_at,
            "ended_at_ts_ms": _current_ms(),
        }

    def _build_report(self, mode: str, requested: int, life_states: tuple) -> RunReport:
        return RunReport(
            mode=mode,
            seed=self._active_seed,
            requested_lives=requested,
            completed_lives=len(life_states),
            root_dir=self.artifacts.root_dir,
            life_states=life_states,
        )

    def _episode_summary(self, life_state, obs) -> EpisodeSummary:
        reason = life_state.end_reason if life_state.end_reason in _DEPLETION_REASONS else None
        return EpisodeSummary(
            episode_id=life_state.life_id,
            biome_id=None if self.env.state is None else self.env.state.biome_id,
            steps=life_state.tick,
            total_reward=0.0,
            died=reason is not None,
            death_reason=reason,
        )

    def _should_finish(self, obs, tick: int, life_max_ticks: int) -> bool:
        if not obs.body.alive:
            return True
        return tick >= life_max_ticks

    def _end_reason(self, obs, tick: int, life_max_ticks: int) -> str:
        if obs.body.energy <= 0:
            return "energy_depleted"
        if obs.body.water <= 0:
            return "water_depleted"
        if tick >= life_max_ticks:
            return "max_ticks_reached"
        return "operator_reset"

    def _anchor_events(self) -> tuple:
        events = self.agent.consume_pending_events()
        return tuple(event.event_type for event in events)

    def _consumed_resource(self, info):
        if info.consumed_food:
            return ResourceType.FOOD
        if info.consumed_water:
            return ResourceType.WATER
        return None

    def _life_count(self, life_count: int | None) -> int:
        if life_count is None:
            return self.experiment_config.train_episodes
        return max(0, life_count)

    def _life_seed(self, life_id: int) -> int:
        seed = np.random.SeedSequence((self.experiment_config.base_seed, life_id))
        return int(seed.generate_state(1, dtype=np.uint32)[0])

    def _set_state(self, state: RunState) -> None:
        if self.run_state_store is not None:
            self.run_state_store.set_state(state)

    def _set_life(self, life_id: int) -> None:
        if self.run_state_store is not None:
            self.run_state_store.set_episode(life_id)

    def _ensure_mode(self, mode: str) -> None:
        supported = {"continuous_full", "continuous_no_regen", "v1_baseline_full"}
        if mode not in supported:
            raise ValueError(f"Unsupported life mode: {mode}")


_DEPLETION_REASONS = {"energy_depleted", "water_depleted"}


def _current_ms() -> int:
    return time_ns() // 1_000_000
