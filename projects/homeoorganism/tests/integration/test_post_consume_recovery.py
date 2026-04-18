import numpy as np

from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings
from homeoorganism.domain.enums import ActionType, BiomeId, CellType, Direction, ResourceType, TargetSource
from homeoorganism.domain.types import BodyState, Pose, Transition, Vec2
from homeoorganism.env.world_state import GridWorldState, set_cell


def _scripted_state(body: BodyState) -> GridWorldState:
    tiles = np.full((11, 11), int(CellType.EMPTY), dtype=np.int16)
    tiles[0, :] = tiles[-1, :] = tiles[:, 0] = tiles[:, -1] = int(CellType.WALL)
    set_cell(tiles, Vec2(5, 4), CellType.FOOD)
    set_cell(tiles, Vec2(7, 4), CellType.WATER)
    return GridWorldState(
        biome_id=BiomeId.A,
        landmark_id=1,
        tiles=tiles,
        pose=Pose(5, 5, Direction.N),
        body=body,
        step_idx=0,
    )


def _runtime(tmp_path, run_id: str):
    return build_runtime(
        "configs/full.yaml",
        RuntimeSettings(tmp_path, run_id=run_id, run_ablations=False, clean_artifacts=True),
    )


def _begin_scripted_episode(runtime, state: GridWorldState):
    runtime.orchestrator.env.state = state
    obs = runtime.orchestrator.env.encoder.encode(state)
    runtime.orchestrator.agent.begin_episode(obs)
    runtime.orchestrator.metrics.begin_episode(obs)
    runtime.orchestrator.agent.fast_memory.observe_resource(ResourceType.FOOD, Vec2(5, 4), 0)
    return obs


def _step(runtime, obs, action: ActionType):
    next_obs, reward, terminated, truncated, info = runtime.orchestrator.env.step(action)
    transition = Transition(obs, action, next_obs, reward, terminated, truncated, info)
    runtime.orchestrator.agent.observe_transition(transition)
    runtime.orchestrator.agent.consume_pending_events()
    return next_obs, info


def _consume_food(runtime, obs):
    action = runtime.orchestrator.agent.act(obs)
    assert action == ActionType.INTERACT
    next_obs, info = _step(runtime, obs, action)
    assert info.consumed_food is True
    return next_obs


def test_post_consume_recovery_no_wait_tail(tmp_path):
    runtime = _runtime(tmp_path, "post-consume-recovery")
    try:
        obs = _begin_scripted_episode(runtime, _scripted_state(BodyState(40, 55, False, True)))
        obs = _consume_food(runtime, obs)
        actions = [runtime.orchestrator.agent.act(obs)]
        obs, _ = _step(runtime, obs, actions[-1])
        actions.append(runtime.orchestrator.agent.act(obs))
        assert ActionType.WAIT not in actions
        assert any(action in {ActionType.TURN_LEFT, ActionType.TURN_RIGHT, ActionType.MOVE_FORWARD} for action in actions)
    finally:
        runtime.monitoring.recorder.close()


def test_consumed_target_invalidates_or_retargets(tmp_path):
    runtime = _runtime(tmp_path, "consumed-target-retarget")
    try:
        obs = _begin_scripted_episode(runtime, _scripted_state(BodyState(40, 55, False, True)))
        obs = _consume_food(runtime, obs)
        next_action = runtime.orchestrator.agent.act(obs)
        selected = runtime.orchestrator.agent.working_buffer.state.selected_proposal
        assert runtime.orchestrator.agent.fast_memory.query(ResourceType.FOOD, obs.pose, obs.step_idx) is None
        assert selected.exact_cell != Vec2(5, 4)
        assert selected.source in {TargetSource.FAST, TargetSource.EXPLORE}
        assert next_action != ActionType.WAIT
    finally:
        runtime.monitoring.recorder.close()


def test_explore_fallback_after_need_none(tmp_path):
    runtime = _runtime(tmp_path, "explore-after-need-none")
    try:
        obs = _begin_scripted_episode(runtime, _scripted_state(BodyState(40, 90, False, True)))
        obs = _consume_food(runtime, obs)
        action = runtime.orchestrator.agent.act(obs)
        selected = runtime.orchestrator.agent.working_buffer.state.selected_proposal
        assert runtime.orchestrator.agent.working_buffer.state.need_state.active_need is None
        assert selected.source == TargetSource.EXPLORE
        assert action != ActionType.WAIT
    finally:
        runtime.monitoring.recorder.close()
