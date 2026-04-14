from homeogrid.agent.belief_map import BeliefMap
from homeogrid.decision.arbiter import Arbiter
from homeogrid.decision.biome_inferer import BiomeInferer
from homeogrid.decision.drive_model import DriveModel
from homeogrid.decision.event_detector import EventDetector
from homeogrid.decision.explorer_policy import ExplorerPolicy
from homeogrid.domain.enums import CellType, Direction, EventType, ResourceType, TargetSource
from homeogrid.domain.types import (
    BodyState,
    NeedState,
    Observation,
    Plan,
    Pose,
    SalientEvent,
    StepInfo,
    TargetProposal,
    Transition,
    Vec2,
)
from homeogrid.memory.fast_memory import FastMemory
from homeogrid.memory.replay_manager import ReplayManager
from homeogrid.memory.slow_memory import SlowMemory
from homeogrid.planning.controller import LowLevelController
from homeogrid.planning.planner import Planner


def _obs(step=0):
    import numpy as np

    return Observation(
        tiles=np.full((5, 5), int(CellType.EMPTY), dtype=np.int16),
        landmark_ids=np.zeros((5, 5), dtype=np.int16),
        pose=Pose(5, 5, Direction.N),
        body=BodyState(70, 50, False, True),
        step_idx=step,
    )


def test_belief_map_updates_and_frontier():
    belief = BeliefMap()
    belief.update(_obs())
    assert belief.known_mask[5, 5]
    assert belief.get_frontier_cells()


def test_drive_model_selects_water_need():
    need = DriveModel().compute(BodyState(70, 20, False, True))
    assert need.active_need == ResourceType.WATER


def test_fast_memory_query_and_invalidation(memory_config):
    memory = FastMemory(memory_config)
    memory.observe_resource(ResourceType.FOOD, Vec2(3, 3), 1)
    proposal = memory.query(ResourceType.FOOD, Pose(5, 5, Direction.N), 2)
    assert proposal is not None
    memory.invalidate_resource(ResourceType.FOOD, Vec2(3, 3), 3)
    assert memory.query(ResourceType.FOOD, Pose(5, 5, Direction.N), 4) is None


def test_slow_memory_update_and_query(memory_config):
    belief = BeliefMap()
    belief.update(_obs())
    memory = SlowMemory(memory_config, "hash")
    sample = type("Sample", (), {"biome_id": "A", "resource_type": ResourceType.FOOD, "position": Vec2(2, 2), "weight": 1.0})
    from homeogrid.domain.enums import BiomeId
    from homeogrid.domain.types import ReplaySample

    memory.update([ReplaySample(BiomeId.A, ResourceType.FOOD, Vec2(2, 2), 1.0)])
    proposal = memory.query(BiomeId.A, ResourceType.FOOD, belief)
    assert proposal is not None
    assert proposal.region_cells


def test_event_detector_emits_collision():
    detector = EventDetector()
    transition = Transition(
        prev_obs=_obs(0),
        action=0,
        next_obs=_obs(1),
        reward=0.0,
        terminated=False,
        truncated=False,
        info=StepInfo(True, False, False, False, 1, 1, False, None),
    )
    events = detector.detect(
        transition,
        NeedState(0.0, 0.5, ResourceType.WATER, False),
        NeedState(0.4, 0.0, ResourceType.FOOD, False),
        None,
        BeliefMap(),
    )
    assert any(event.event_type == EventType.COLLISION for event in events)
    assert any(event.event_type == EventType.NEED_SWITCH for event in events)


def test_replay_manager_builds_samples():
    events = [
        SalientEvent(EventType.RESOURCE_OBSERVED, 1, "A", Pose(1, 1, Direction.N), ResourceType.FOOD, None, 2.0, Vec2(2, 2))
    ]
    samples = ReplayManager().build_samples(events)
    assert len(samples) == 1


def test_arbiter_prefers_fast(memory_config):
    arbiter = Arbiter(memory_config)
    need = NeedState(0.5, 0.1, ResourceType.FOOD, False)
    fast = TargetProposal(TargetSource.FAST, ResourceType.FOOD, 0.9, exact_cell=Vec2(2, 2))
    slow = TargetProposal(TargetSource.SLOW, ResourceType.FOOD, 0.9, region_cells=(Vec2(3, 3),))
    choice = arbiter.choose(need, fast, slow, BeliefMap())
    assert choice.source == TargetSource.FAST


def test_planner_and_controller_generate_motion(planner_config):
    belief = BeliefMap()
    belief.update(_obs())
    planner = Planner(planner_config)
    controller = LowLevelController()
    proposal = TargetProposal(TargetSource.EXPLORE, None, 0.1, exact_cell=Vec2(6, 5))
    plan = planner.plan(belief, Pose(5, 5, Direction.N), proposal)
    action = controller.next_action(Pose(5, 5, Direction.N), proposal, plan)
    assert plan.valid
    assert action in {0, 1, 2}


def test_biome_inferer_reads_landmark():
    obs = _obs()
    obs.landmark_ids[2, 2] = 2
    biome = BiomeInferer().infer(obs, BeliefMap())
    assert biome.value == "B"
