"""Runtime assembly."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from threading import Thread

import uvicorn

from homeogrid.app.runtime_settings import RuntimeSettings
from homeogrid.agent.belief_map import BeliefMap
from homeogrid.agent.core import AgentCore
from homeogrid.agent.working_buffer import WorkingBuffer
from homeogrid.analytics.metrics import MetricsCollector
from homeogrid.analytics.report_writer import ReportWriter
from homeogrid.config.loader import ConfigBundle, load_config
from homeogrid.decision.arbiter import Arbiter
from homeogrid.decision.biome_inferer import BiomeInferer
from homeogrid.decision.drive_model import DriveModel
from homeogrid.decision.event_detector import EventDetector
from homeogrid.decision.explorer_policy import ExplorerPolicy
from homeogrid.decision.status_translator import StatusTranslator
from homeogrid.env.gym_env import HomeoGridEnv
from homeogrid.memory.fast_memory import FastMemory
from homeogrid.memory.replay_manager import ReplayManager
from homeogrid.memory.slow_memory import SlowMemory
from homeogrid.monitoring.core.alert_engine import AlertEngine
from homeogrid.monitoring.core.frame_ring_buffer import FrameRingBuffer
from homeogrid.monitoring.core.monitoring_facade import MonitoringFacade
from homeogrid.monitoring.core.replay_loader import ReplayLoader
from homeogrid.monitoring.core.session_recorder import SessionRecorder
from homeogrid.monitoring.core.snapshot_builder import SnapshotBuilder
from homeogrid.monitoring.core.stream_hub import StreamHub
from homeogrid.monitoring.domain.enums import OperatorCommandType, RunState
from homeogrid.monitoring.web.api import create_monitor_app
from homeogrid.orchestration.command_bus import CommandBus
from homeogrid.orchestration.experiment_orchestrator import ExperimentOrchestrator
from homeogrid.orchestration.run_artifacts import RunArtifacts
from homeogrid.orchestration.run_state_store import RunStateStore
from homeogrid.planning.controller import LowLevelController
from homeogrid.planning.planner import Planner


@dataclass
class Runtime:
    config: ConfigBundle
    orchestrator: ExperimentOrchestrator
    monitoring: MonitoringFacade
    control_port: "ControlPort"
    artifacts: RunArtifacts


@dataclass
class ControlPort:
    command_bus: CommandBus
    run_state_store: RunStateStore
    orchestrator: ExperimentOrchestrator

    def get_run_state(self) -> str:
        return self.run_state_store.get_run_state().value

    def pause(self) -> bool:
        accepted = self.command_bus.submit(OperatorCommandType.PAUSE)
        if accepted:
            self.run_state_store.set_state(RunState.PAUSED)
        return accepted

    def resume(self) -> bool:
        accepted = self.command_bus.submit(OperatorCommandType.RESUME)
        if accepted:
            self.run_state_store.set_state(RunState.RUNNING)
        return accepted

    def reset_episode(self) -> bool:
        return self.command_bus.submit(OperatorCommandType.RESET_EPISODE)

    def save_snapshot(self) -> str | None:
        return self.orchestrator.save_snapshot()

    def toggle_debug(self, enabled: bool | None = None) -> bool:
        accepted = self.command_bus.submit(OperatorCommandType.TOGGLE_DEBUG, enabled)
        if accepted and enabled is not None:
            self.run_state_store.toggle_debug(enabled)
        return accepted


def build_runtime(config_path: str, settings: RuntimeSettings | None = None) -> Runtime:
    runtime_settings = settings or RuntimeSettings()
    config = _apply_runtime_settings(load_config(config_path), runtime_settings)
    artifacts = RunArtifacts(Path(runtime_settings.artifacts_root), config.experiment.run_id)
    artifacts.setup(runtime_settings.clean_artifacts)
    artifacts.write_yaml(artifacts.config_snapshot_path, _yaml_ready(asdict(config)))
    artifacts.write_json(artifacts.manifest_path, _runtime_manifest(config, config_path, artifacts))
    components = _runtime_components(config, artifacts)
    orchestrator = ExperimentOrchestrator(
        env=components["env"],
        agent=components["agent"],
        metrics=components["metrics"],
        monitoring=components["monitoring"],
        snapshot_builder=components["snapshot_builder"],
        report_writer=ReportWriter(str(artifacts.root_dir)),
        command_bus=components["command_bus"],
        run_state_store=components["run_state_store"],
        experiment_config=config.experiment,
        artifacts=artifacts,
    )
    control_port = ControlPort(components["command_bus"], components["run_state_store"], orchestrator)
    return Runtime(config, orchestrator, components["monitoring"], control_port, artifacts)


def run_runtime(config_path: str, mode: str) -> None:
    runtime = build_runtime(config_path)
    if mode == "ablate":
        return _run_ablation_only(runtime)
    if not runtime.config.experiment.enable_monitoring:
        return _run_without_server(runtime)
    app = create_monitor_app(
        runtime.monitoring,
        runtime.control_port,
        str(Path(__file__).resolve().parent.parent / "monitoring" / "web" / "static"),
    )
    worker = Thread(target=_run_full_suite, args=(runtime.orchestrator, runtime.config.experiment.run_ablations))
    worker.daemon = True
    worker.start()
    uvicorn.run(app, host=runtime.config.monitor.bind_host, port=runtime.config.monitor.bind_port)


def _run_full_suite(orchestrator: ExperimentOrchestrator, run_ablations: bool) -> None:
    orchestrator.run_protocol("full")
    if not run_ablations:
        orchestrator.monitoring.recorder.close()
        return
    for mode in ("full", "no_fast", "no_slow", "no_interoception", "no_rough_cost", "full_observation"):
        orchestrator.run_ablation(mode)
    orchestrator.monitoring.recorder.close()


def _build_agent(config, belief_map, working_buffer, slow_memory) -> AgentCore:
    return AgentCore(
        drive_model=DriveModel(),
        belief_map=belief_map,
        biome_inferer=BiomeInferer(),
        working_buffer=working_buffer,
        fast_memory=FastMemory(config.memory),
        slow_memory=slow_memory,
        arbiter=Arbiter(config.memory),
        explorer=ExplorerPolicy(),
        planner=Planner(config.planner),
        controller=LowLevelController(),
        event_detector=EventDetector(),
        replay_manager=ReplayManager(),
    )


def _build_snapshot_builder(config, belief_map, working_buffer, metrics, run_state_store, translator):
    return SnapshotBuilder(
        belief_map=belief_map,
        working_buffer=working_buffer,
        metrics=metrics,
        run_state_store=run_state_store,
        translator=translator,
        episode_limit=config.env.episode_limit,
    )


def _build_monitoring(config, translator, run_state_store, artifacts: RunArtifacts) -> MonitoringFacade:
    return MonitoringFacade(
        frame_buffer=FrameRingBuffer(config.monitor.frame_buffer_size),
        alert_engine=AlertEngine(translator),
        recorder=SessionRecorder(str(artifacts.monitoring_dir), config.monitor.raw_event_buffer_size),
        stream_hub=StreamHub(),
        replay_loader=ReplayLoader(str(artifacts.monitoring_dir)),
        run_state_store=run_state_store,
        max_alerts=config.monitor.max_alerts_in_panel,
    )


def _run_ablation_only(runtime: Runtime) -> None:
    for ablation in runtime.config.experiment.ablation_modes:
        runtime.orchestrator.run_ablation(ablation)
    runtime.orchestrator.report_writer.write_ablations(runtime.orchestrator._ablation_rows)
    runtime.monitoring.recorder.close()


def _run_without_server(runtime: Runtime) -> None:
    _run_full_suite(runtime.orchestrator, runtime.config.experiment.run_ablations)
    runtime.monitoring.recorder.close()


def _runtime_components(config, artifacts: RunArtifacts):
    belief_map = BeliefMap(config.env.grid_size)
    working_buffer = WorkingBuffer()
    metrics = MetricsCollector()
    translator = StatusTranslator()
    run_state_store = RunStateStore()
    command_bus = CommandBus()
    env = HomeoGridEnv(config.env, config.body, config.reward)
    slow_memory = SlowMemory(config.memory, config.config_hash)
    slow_memory.load(str(artifacts.slow_memory_path))
    return {
        "agent": _build_agent(config, belief_map, working_buffer, slow_memory),
        "command_bus": command_bus,
        "env": env,
        "metrics": metrics,
        "monitoring": _build_monitoring(config, translator, run_state_store, artifacts),
        "run_state_store": run_state_store,
        "snapshot_builder": _build_snapshot_builder(config, belief_map, working_buffer, metrics, run_state_store, translator),
    }


def _apply_runtime_settings(config: ConfigBundle, settings: RuntimeSettings) -> ConfigBundle:
    experiment = config.experiment
    if settings.run_id is not None:
        experiment = replace(experiment, run_id=settings.run_id)
    if settings.base_seed is not None:
        experiment = replace(experiment, base_seed=settings.base_seed)
    if settings.run_ablations is not None:
        experiment = replace(experiment, run_ablations=settings.run_ablations)
    return replace(config, experiment=experiment)


def _runtime_manifest(config: ConfigBundle, config_path: str, artifacts: RunArtifacts) -> dict:
    return {
        "config_path": str(Path(config_path)),
        "config_hash": config.config_hash,
        "run_id": config.experiment.run_id,
        "base_seed": config.experiment.base_seed,
        "artifacts_root": str(artifacts.root_dir),
    }


def _yaml_ready(value):
    if isinstance(value, dict):
        return {key: _yaml_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_yaml_ready(item) for item in value]
    if isinstance(value, list):
        return [_yaml_ready(item) for item in value]
    return value
