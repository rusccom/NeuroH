"""Experiment orchestration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from threading import Event
from time import sleep

from homeogrid.agent.core import AgentCore
from homeogrid.analytics.metrics import MetricsCollector
from homeogrid.analytics.report_writer import ReportWriter
from homeogrid.config.experiment_config import ExperimentConfig
from homeogrid.domain.enums import EventType
from homeogrid.domain.types import EpisodeSummary, Transition
from homeogrid.env.gym_env import HomeoGridEnv
from homeogrid.monitoring.core.monitoring_facade import MonitoringFacade
from homeogrid.monitoring.core.snapshot_builder import SnapshotBuilder
from homeogrid.monitoring.domain.dto import EpisodeSummaryView, OperatorEvent
from homeogrid.monitoring.domain.enums import AlertLevel, OperatorCommandType, RunState
from homeogrid.orchestration.command_bus import CommandBus
from homeogrid.orchestration.run_artifacts import RunArtifacts
from homeogrid.orchestration.run_state_store import RunStateStore


@dataclass
class ExperimentOrchestrator:
    env: HomeoGridEnv
    agent: AgentCore
    metrics: MetricsCollector
    monitoring: MonitoringFacade
    snapshot_builder: SnapshotBuilder
    report_writer: ReportWriter
    command_bus: CommandBus
    run_state_store: RunStateStore
    experiment_config: ExperimentConfig
    artifacts: RunArtifacts

    def __post_init__(self) -> None:
        self._stop = Event()
        self._metric_rows: list[dict] = []
        self._ablation_rows: list[dict] = []
        self._active_mode = "full"
        self._active_phase = "train"
        self._active_seed = self.experiment_config.base_seed
        self._full_planner_config = self.agent.planner.planner_config

    def run_train(self) -> None:
        self.run_protocol("full", eval_seen_episodes=0, eval_relocation_episodes=0)

    def run_eval(self) -> None:
        self.run_protocol("full", train_episodes=0)

    def run_ablation(self, mode: str) -> None:
        start_index = len(self._metric_rows)
        self.run_protocol(mode, train_episodes=0, eval_relocation_episodes=0)
        self._ablation_rows.extend(self._metric_rows[start_index:])
        self.report_writer.write_ablations(self._ablation_rows)

    def run_protocol(
        self,
        mode: str,
        train_episodes: int | None = None,
        eval_seen_episodes: int | None = None,
        eval_relocation_episodes: int | None = None,
    ) -> None:
        self._activate_mode(mode)
        self.run_state_store.set_state(RunState.RUNNING)
        self._run_phase("train", self._episode_count(train_episodes, self.experiment_config.train_episodes), 0)
        self._run_phase("eval_seen", self._episode_count(eval_seen_episodes, self.experiment_config.eval_episodes_seen), 10_000)
        self._run_relocation_phase(eval_relocation_episodes)
        self._restore_full_mode()
        self._finalize()

    def run_single_episode(self, seed: int) -> EpisodeSummary:
        episode_id = self.run_state_store.get_episode() + 1
        obs = self._prepare_episode(episode_id, seed)
        total_reward = 0.0
        reset_requested = False
        while True:
            if self._stop.is_set():
                break
            if self._apply_commands():
                reset_requested = True
                break
            obs, step_reward, terminated, truncated = self._step_once(obs, episode_id)
            total_reward += step_reward
            if terminated or truncated:
                break
        summary = self._episode_summary(episode_id, obs, total_reward)
        self.agent.end_episode(summary)
        return self._complete_episode(summary, reset_requested)

    def get_run_state(self) -> str:
        return self.run_state_store.get_run_state().value

    def pause(self) -> bool:
        self.run_state_store.set_state(RunState.PAUSED)
        return True

    def resume(self) -> bool:
        self.run_state_store.set_state(RunState.RUNNING)
        return True

    def reset_episode(self) -> bool:
        return self.command_bus.submit(OperatorCommandType.RESET_EPISODE)

    def save_snapshot(self) -> str | None:
        latest = self.monitoring.frame_buffer.latest()
        if latest is None:
            return None
        path = self.artifacts.snapshots_dir / latest.run_id / str(latest.episode_id) / f"{latest.world.step_idx}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(latest.model_dump_json(indent=2), encoding="utf-8")
        return str(path)

    def toggle_debug(self, enabled: bool | None = None) -> bool:
        return self.run_state_store.toggle_debug(enabled)

    def stop(self) -> None:
        self._stop.set()

    def _run_phase(self, phase: str, episodes: int, offset: int) -> None:
        if episodes <= 0:
            return
        self._active_phase = phase
        self._run_batch(episodes, self.experiment_config.base_seed + offset)

    def _run_batch(self, episodes: int, base_seed: int) -> None:
        for index in range(episodes):
            self._active_seed = base_seed + index
            self.run_single_episode(self._active_seed)
            if self._stop.is_set():
                break

    def _complete_episode(self, summary: EpisodeSummary, reset_requested: bool) -> EpisodeSummary:
        row = self.metrics.end_episode(summary)
        row["mode"] = self._active_mode
        row["phase"] = self._active_phase
        row["seed"] = self._active_seed
        row["run_id"] = self.experiment_config.run_id
        row["config_hash"] = self.agent.slow_memory.config_hash
        row["reset_requested"] = reset_requested
        self._metric_rows.append(row)
        self.report_writer.append_summary(row)
        summary_view = EpisodeSummaryView(
            episode_id=summary.episode_id,
            biome_id=summary.biome_id.value if summary.biome_id else None,
            steps=summary.steps,
            total_reward=summary.total_reward,
            died=summary.died,
            death_reason=summary.death_reason,
        )
        self.monitoring.publish_episode_end(summary_view)
        return summary

    def _publish_events(self, events, episode_id: int) -> None:
        latest = self.monitoring.frame_buffer.latest()
        ts_ms = 0 if latest is None else latest.ts_ms
        for event in events:
            level = AlertLevel.INFO if event.event_type != EventType.DEATH else AlertLevel.CRITICAL
            payload = OperatorEvent(
                level=level,
                code=event.event_type.value,
                message=event.event_type.value,
                step_idx=event.step_idx,
                ts_ms=ts_ms,
            )
            self.monitoring.publish_event(payload, self.experiment_config.run_id, episode_id)

    def _apply_commands(self) -> bool:
        reset_requested = False
        for command in self.command_bus.drain():
            reset_requested = self._handle_command(command.command_type, command.enabled, reset_requested)
        return self._wait_if_paused(reset_requested)

    def _set_relocation(self, enabled: bool) -> None:
        self.env.env_config = replace(self.env.env_config, enable_relocation=enabled)

    def _activate_mode(self, mode: str) -> None:
        self._active_mode = mode
        self._apply_ablation(mode)

    def _apply_ablation(self, mode: str) -> None:
        self.agent.fast_memory.enabled = mode != "no_fast"
        self.agent.slow_memory.enabled = mode != "no_slow"
        self.agent.drive_model.enabled = mode != "no_interoception"
        if mode == "no_rough_cost":
            self.agent.planner.planner_config = replace(self.agent.planner.planner_config, rough_cost=1.0)

    def _restore_full_mode(self) -> None:
        self._active_mode = "full"
        self.agent.fast_memory.enabled = True
        self.agent.slow_memory.enabled = True
        self.agent.drive_model.enabled = True
        self.agent.planner.planner_config = self._full_planner_config

    def _maybe_full_observation(self) -> None:
        if self._active_mode != "full_observation" or self.env.state is None:
            return
        self.agent.belief_map.known_mask[:] = True
        self.agent.belief_map.tile_ids[:] = self.env.state.tiles

    def _run_relocation_phase(self, eval_relocation_episodes: int | None) -> None:
        count = self._episode_count(eval_relocation_episodes, self.experiment_config.eval_episodes_relocation)
        if count <= 0:
            return
        self._set_relocation(True)
        self._run_phase("eval_relocation", count, 20_000)
        self._set_relocation(False)

    def _episode_count(self, override: int | None, default: int) -> int:
        if override is None:
            return default
        return max(0, override)

    def _finalize(self) -> None:
        self.agent.slow_memory.save(str(self.artifacts.slow_memory_path))
        self.report_writer.write_metrics(self._metric_rows)
        self.report_writer.write_ablations(self._ablation_rows)
        self.run_state_store.set_state(RunState.ENDED)

    def _prepare_episode(self, episode_id: int, seed: int):
        self.run_state_store.set_episode(episode_id)
        obs, _ = self.env.reset(seed=seed)
        self.agent.begin_episode(obs)
        self.metrics.begin_episode(obs)
        self._maybe_full_observation()
        return obs

    def _step_once(self, obs, episode_id: int) -> tuple:
        action = self.agent.act(obs)
        next_obs, reward, terminated, truncated, info = self.env.step(action)
        transition = Transition(obs, action, next_obs, reward, terminated, truncated, info)
        self.agent.observe_transition(transition)
        events = self.agent.consume_pending_events()
        selected = self.agent.working_buffer.state.selected_proposal
        source = selected.source if selected else None
        self.metrics.on_step(transition, source, events)
        snapshot = self.snapshot_builder.build(self.experiment_config.run_id, episode_id, next_obs)
        self.monitoring.publish_step(snapshot)
        self._publish_events(events, episode_id)
        return next_obs, reward, terminated, truncated

    def _episode_summary(self, episode_id: int, obs, total_reward: float) -> EpisodeSummary:
        return EpisodeSummary(
            episode_id=episode_id,
            biome_id=self.agent.working_buffer.state.biome_id,
            steps=obs.step_idx,
            total_reward=total_reward,
            died=not obs.body.alive,
            death_reason=None if obs.body.alive else "body_depleted",
        )

    def _handle_command(self, command_type, enabled, reset_requested: bool) -> bool:
        if command_type == OperatorCommandType.PAUSE:
            self.pause()
        elif command_type == OperatorCommandType.RESUME:
            self.resume()
        elif command_type == OperatorCommandType.RESET_EPISODE:
            reset_requested = True
        elif command_type == OperatorCommandType.SAVE_SNAPSHOT:
            self.save_snapshot()
        elif command_type == OperatorCommandType.TOGGLE_DEBUG:
            self.toggle_debug(enabled)
        return reset_requested

    def _wait_if_paused(self, reset_requested: bool) -> bool:
        while self.run_state_store.get_run_state() == RunState.PAUSED:
            sleep(0.05)
            for command in self.command_bus.drain():
                reset_requested = self._resume_command(command.command_type, command.enabled, reset_requested)
        return reset_requested

    def _resume_command(self, command_type, enabled, reset_requested: bool) -> bool:
        if command_type == OperatorCommandType.RESUME:
            self.resume()
        elif command_type == OperatorCommandType.RESET_EPISODE:
            reset_requested = True
            self.resume()
        elif command_type == OperatorCommandType.SAVE_SNAPSHOT:
            self.save_snapshot()
        elif command_type == OperatorCommandType.TOGGLE_DEBUG:
            self.toggle_debug(enabled)
        return reset_requested
