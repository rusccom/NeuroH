import json
from pathlib import Path

from homeoorganism.decision.status_translator import StatusTranslator
from homeoorganism.monitoring.core.alert_engine import AlertEngine
from homeoorganism.monitoring.core.frame_ring_buffer import FrameRingBuffer
from homeoorganism.monitoring.core.replay_loader import ReplayLoader
from homeoorganism.monitoring.core.session_recorder import SessionRecorder
from homeoorganism.monitoring.domain.dto import (
    BeliefMapView,
    BlobVisualState,
    BodyTelemetry,
    MemoryTelemetry,
    NeedTelemetry,
    PlannerTelemetry,
    StepSnapshot,
    WorldTelemetry,
)
from homeoorganism.monitoring.domain.enums import BehaviorMode, DecisionSource, RunState, StreamEventType


def _snapshot():
    return StepSnapshot(
        ts_ms=1,
        run_id="r",
        episode_id=1,
        run_state=RunState.RUNNING,
        behavior_mode=BehaviorMode.EXPLORE,
        body=_body(),
        need=_need(),
        memory=_memory(),
        planner=PlannerTelemetry(plan_valid=False, plan_cost=0.0, path_len=0, frontier_count=8),
        world=_world(),
        belief_map=_belief(),
        blob=_blob(),
    )


def _body():
    return BodyTelemetry(energy=10, water=40, alive=True, last_collision=True)


def _need():
    return NeedTelemetry(energy_deficit=0.8, water_deficit=0.2, active_need="food", critical=True, dominance=0.6)


def _memory():
    return MemoryTelemetry(
        guidance_source=DecisionSource.FAST,
        decision_source=DecisionSource.FAST,
        execution_mode="direct",
        fast_confidence=0.8,
        slow_confidence=0.7,
        selected_confidence=0.8,
        fast_target=[1, 1],
        slow_region_size=4,
    )


def _world():
    return WorldTelemetry(biome_id="A", pose=[5, 5, 0], target=[7, 7], path=[], step_idx=6, total_reward=-1.0)


def _belief():
    return BeliefMapView(known_mask=[[1]], tile_ids=[[0]], frontier_cells=[[1, 1]], observed_food=[[2, 2]], observed_water=[[3, 3]])


def _blob():
    return BlobVisualState(stress=0.5, uncertainty=0.5, instability=0.5, scale_x=1.0, scale_y=1.0, scale_z=1.0, pulse_hz=1.0, noise_amp=1.0, halo_level=1.0)


def test_status_translator_maps_behavior():
    translator = StatusTranslator()
    assert translator.alert_message("LOW_ENERGY_WARN")


def test_alert_engine_emits_low_energy():
    alerts = AlertEngine(StatusTranslator()).evaluate(_snapshot())
    assert any(item.code == "LOW_ENERGY_CRITICAL" for item in alerts)


def test_frame_ring_buffer_latest_and_tail():
    buffer = FrameRingBuffer(3)
    snap = _snapshot()
    buffer.append(snap)
    assert buffer.latest() == snap
    assert buffer.tail(1) == [snap]


def test_session_recorder_writes_jsonl(tmp_path: Path):
    recorder = SessionRecorder(str(tmp_path), 8, frame_stride=3)
    for step_idx in range(1, 8):
        recorder.record("run", 1, StreamEventType.FRAME, {"world": {"step_idx": step_idx}})
    recorder.record("run", 1, StreamEventType.SUMMARY, {"episode_id": 1})
    recorder.close()
    lines = (tmp_path / "run" / "1.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    frame_steps = [record["payload"]["world"]["step_idx"] for record in records if record["type"] == "frame"]
    assert frame_steps == [1, 3, 6, 7]


def test_replay_loader_returns_frame_records(tmp_path: Path):
    recorder = SessionRecorder(str(tmp_path), 8, frame_stride=4)
    recorder.record("run", 2, StreamEventType.FRAME, {"world": {"step_idx": 1}})
    recorder.record("run", 2, StreamEventType.FRAME, {"world": {"step_idx": 2}})
    recorder.record("run", 2, StreamEventType.SUMMARY, {"episode_id": 2})
    recorder.close()
    history = ReplayLoader(str(tmp_path)).load("run", 2)
    assert any(record["type"] == "frame" for record in history["records"])
