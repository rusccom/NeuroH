import numpy as np

from homeogrid.app.run import build_runtime
from homeogrid.app.runtime_settings import RuntimeSettings
from homeogrid.domain.enums import ActionType, BiomeId, CellType, Direction, EventType, ResourceType
from homeogrid.domain.types import BodyState, Pose, Transition, Vec2
from homeogrid.env.world_state import GridWorldState, set_cell


def _scripted_state() -> GridWorldState:
    tiles = np.full((11, 11), int(CellType.EMPTY), dtype=np.int16)
    tiles[0, :] = tiles[-1, :] = tiles[:, 0] = tiles[:, -1] = int(CellType.WALL)
    set_cell(tiles, Vec2(5, 4), CellType.FOOD)
    return GridWorldState(
        biome_id=BiomeId.A,
        landmark_id=1,
        tiles=tiles,
        pose=Pose(5, 5, Direction.N),
        body=BodyState(40, 70, False, True),
        step_idx=0,
    )


def test_scripted_consume_episode_emits_resource_consumed(tmp_path):
    runtime = build_runtime(
        "configs/full.yaml",
        RuntimeSettings(tmp_path, run_id="scripted-consume", run_ablations=False, clean_artifacts=True),
    )
    try:
        state = _scripted_state()
        runtime.orchestrator.env.state = state
        obs = runtime.orchestrator.env.encoder.encode(state)
        runtime.orchestrator.agent.begin_episode(obs)
        runtime.orchestrator.metrics.begin_episode(obs)
        runtime.orchestrator.agent.fast_memory.observe_resource(ResourceType.FOOD, Vec2(5, 4), 0)
        action = runtime.orchestrator.agent.act(obs)
        assert action == ActionType.INTERACT
        next_obs, reward, terminated, truncated, info = runtime.orchestrator.env.step(action)
        transition = Transition(obs, action, next_obs, reward, terminated, truncated, info)
        runtime.orchestrator.agent.observe_transition(transition)
        events = runtime.orchestrator.agent.consume_pending_events()
        assert info.consumed_food is True
        assert next_obs.body.energy > obs.body.energy
        assert any(event.event_type == EventType.RESOURCE_CONSUMED for event in events)
    finally:
        runtime.monitoring.recorder.close()


def test_runtime_replay_history_contains_frame_records(tmp_path):
    runtime = build_runtime(
        "configs/full.yaml",
        RuntimeSettings(tmp_path, run_id="replay-history", run_ablations=False, clean_artifacts=True),
    )
    try:
        summary = runtime.orchestrator.run_single_episode(123)
    finally:
        runtime.monitoring.recorder.close()
    history = runtime.monitoring.history(runtime.config.experiment.run_id, summary.episode_id)
    assert any(record["type"] == "frame" for record in history["records"])
