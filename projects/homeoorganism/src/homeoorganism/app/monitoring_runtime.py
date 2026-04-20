"""Monitoring runtime assembly helpers."""

from __future__ import annotations

from homeoorganism.monitoring.core.alert_engine import AlertEngine
from homeoorganism.monitoring.core.frame_ring_buffer import FrameRingBuffer
from homeoorganism.monitoring.core.life_snapshot_builder import LifeSnapshotBuilder
from homeoorganism.monitoring.core.monitoring_facade import MonitoringFacade
from homeoorganism.monitoring.core.replay_loader import ReplayLoader
from homeoorganism.monitoring.core.session_recorder import SessionRecorder
from homeoorganism.monitoring.core.snapshot_builder import SnapshotBuilder
from homeoorganism.monitoring.core.stream_hub import StreamHub


def build_monitoring(config, translator, run_state_store, artifacts) -> MonitoringFacade:
    return MonitoringFacade(
        frame_buffer=FrameRingBuffer(config.monitor.frame_buffer_size),
        alert_engine=AlertEngine(translator),
        recorder=SessionRecorder(str(artifacts.monitoring_dir), config.monitor.raw_event_buffer_size),
        stream_hub=StreamHub(),
        replay_loader=ReplayLoader(str(artifacts.monitoring_dir)),
        run_state_store=run_state_store,
        max_alerts=config.monitor.max_alerts_in_panel,
    )


def build_snapshot_builder(config, belief_map, working_buffer, metrics, run_state_store, translator, env, mode):
    if mode == "episodic_full":
        return SnapshotBuilder(
            belief_map=belief_map,
            working_buffer=working_buffer,
            metrics=metrics,
            run_state_store=run_state_store,
            translator=translator,
            episode_limit=config.env.episode_limit,
        )
    return LifeSnapshotBuilder(
        belief_map=belief_map,
        working_buffer=working_buffer,
        metrics=metrics,
        run_state_store=run_state_store,
        translator=translator,
        env=env,
        life_max_ticks=config.experiment.life_max_ticks,
    )
