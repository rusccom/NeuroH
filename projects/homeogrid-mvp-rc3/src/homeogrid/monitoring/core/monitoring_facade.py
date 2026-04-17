"""Monitoring facade."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from homeogrid.monitoring.core.alert_engine import AlertEngine
from homeogrid.monitoring.core.frame_ring_buffer import FrameRingBuffer
from homeogrid.monitoring.core.replay_loader import ReplayLoader
from homeogrid.monitoring.core.session_recorder import SessionRecorder
from homeogrid.monitoring.core.stream_hub import StreamHub
from homeogrid.monitoring.domain.dto import EpisodeSummaryView
from homeogrid.monitoring.domain.enums import StreamEventType
from homeogrid.monitoring.interfaces import TelemetryPublisher
from homeogrid.orchestration.run_state_store import RunStateStore


@dataclass
class MonitoringFacade(TelemetryPublisher):
    frame_buffer: FrameRingBuffer
    alert_engine: AlertEngine
    recorder: SessionRecorder
    stream_hub: StreamHub
    replay_loader: ReplayLoader
    run_state_store: RunStateStore
    max_alerts: int = 100
    recent_alerts: deque = field(init=False)

    def __post_init__(self) -> None:
        self.recent_alerts = deque(maxlen=self.max_alerts)

    def publish_step(self, snapshot) -> None:
        self.frame_buffer.append(snapshot)
        self.recorder.record(snapshot.run_id, snapshot.episode_id, StreamEventType.FRAME, snapshot.model_dump())
        self.stream_hub.publish(StreamEventType.FRAME, snapshot.model_dump())
        for alert in self.alert_engine.evaluate(snapshot):
            self.publish_event(alert, snapshot.run_id, snapshot.episode_id)

    def publish_event(self, event, run_id: str | None = None, episode_id: int | None = None) -> None:
        self.recent_alerts.appendleft(event)
        if run_id is not None and episode_id is not None:
            self.recorder.record(run_id, episode_id, StreamEventType.ALERT, event.model_dump())
        self.stream_hub.publish(StreamEventType.ALERT, event.model_dump())

    def publish_episode_end(self, summary: EpisodeSummaryView) -> None:
        latest = self.frame_buffer.latest()
        run_id = latest.run_id if latest is not None else "unknown"
        self.recorder.record(run_id, summary.episode_id, StreamEventType.SUMMARY, summary.model_dump())
        self.stream_hub.publish(StreamEventType.SUMMARY, summary.model_dump())

    def bootstrap(self) -> dict:
        latest = self.frame_buffer.latest()
        return {
            "run_state": self.run_state_store.get_run_state(),
            "latest_frame": None if latest is None else latest.model_dump(),
            "recent_alerts": [item.model_dump() for item in self.recent_alerts],
        }

    def history(self, run_id: str, episode_id: int) -> dict:
        return self.replay_loader.load(run_id, episode_id)
