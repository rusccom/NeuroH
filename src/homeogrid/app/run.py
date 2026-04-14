"""Runtime assembly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Thread

import uvicorn

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
from homeogrid.orchestration.run_state_store import RunStateStore
from homeogrid.planning.controller import LowLevelController
from homeogrid.planning.planner import Planner


@dataclass
class Runtime:
    config: ConfigBundle
    orchestrator: ExperimentOrchestrator
    monitoring: MonitoringFacade
    control_port: "ControlPort"


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


def build_runtime(config_path: str) -> Runtime:
    config = load_config(config_path)
    components = _runtime_components(config)
    orchestrator = ExperimentOrchestrator(
        env=components["env"],
        agent=components["agent"],
        metrics=components["metrics"],
        monitoring=components["monitoring"],
        snapshot_builder=components["snapshot_builder"],
        report_writer=ReportWriter(),
        command_bus=components["command_bus"],
        run_state_store=components["run_state_store"],
        experiment_config=config.experiment,
    )
    control_port = ControlPort(components["command_bus"], components["run_state_store"], orchestrator)
    return Runtime(config, orchestrator, components["monitoring"], control_port)


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
    orchestrator.run_train()
    orchestrator.run_eval()
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


def _build_monitoring(config, translator, run_state_store) -> MonitoringFacade:
    return MonitoringFacade(
        frame_buffer=FrameRingBuffer(config.monitor.frame_buffer_size),
        alert_engine=AlertEngine(translator),
        recorder=SessionRecorder("artifacts/monitoring", config.monitor.raw_event_buffer_size),
        stream_hub=StreamHub(),
        replay_loader=ReplayLoader("artifacts/monitoring"),
        run_state_store=run_state_store,
        max_alerts=config.monitor.max_alerts_in_panel,
    )


def _run_ablation_only(runtime: Runtime) -> None:
    for ablation in runtime.config.experiment.ablation_modes:
        runtime.orchestrator.run_ablation(ablation)
    runtime.orchestrator.report_writer.write_ablations(runtime.orchestrator._ablation_rows)
    runtime.monitoring.recorder.close()


def _run_without_server(runtime: Runtime) -> None:
    runtime.orchestrator.run_train()
    runtime.orchestrator.run_eval()
    runtime.monitoring.recorder.close()


def _runtime_components(config):
    belief_map = BeliefMap(config.env.grid_size)
    working_buffer = WorkingBuffer()
    metrics = MetricsCollector()
    translator = StatusTranslator()
    run_state_store = RunStateStore()
    command_bus = CommandBus()
    env = HomeoGridEnv(config.env, config.body, config.reward)
    slow_memory = SlowMemory(config.memory, config.config_hash)
    slow_memory.load("artifacts/memory/slow_memory.npz")
    return {
        "agent": _build_agent(config, belief_map, working_buffer, slow_memory),
        "command_bus": command_bus,
        "env": env,
        "metrics": metrics,
        "monitoring": _build_monitoring(config, translator, run_state_store),
        "run_state_store": run_state_store,
        "snapshot_builder": _build_snapshot_builder(config, belief_map, working_buffer, metrics, run_state_store, translator),
    }
