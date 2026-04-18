import numpy as np

from homeoorganism.analytics.metrics import MetricsCollector
from homeoorganism.domain.enums import ActionType, Direction, EventType
from homeoorganism.domain.types import (
    BodyState,
    EpisodeSummary,
    Observation,
    Pose,
    SalientEvent,
    StepInfo,
    Transition,
)


def _obs(step: int, energy: int, water: int) -> Observation:
    return Observation(
        tiles=np.zeros((5, 5), dtype=np.int16),
        landmark_ids=np.zeros((5, 5), dtype=np.int16),
        pose=Pose(5, 5, Direction.N),
        body=BodyState(energy, water, False, True),
        step_idx=step,
    )


def test_need_switch_count_matches_raw_need_switch_events():
    collector = MetricsCollector()
    prev_obs = _obs(0, 70, 20)
    next_obs = _obs(1, 20, 70)
    collector.begin_episode(prev_obs)
    transition = Transition(
        prev_obs=prev_obs,
        action=ActionType.WAIT,
        next_obs=next_obs,
        reward=0.0,
        terminated=False,
        truncated=False,
        info=StepInfo(False, False, False, False, 1, 1, False, None),
    )
    events = [
        SalientEvent(EventType.NEED_SWITCH, 1, None, next_obs.pose, None, ActionType.WAIT, 1.0, None),
        SalientEvent(EventType.NEED_SWITCH, 1, None, next_obs.pose, None, ActionType.WAIT, 1.0, None),
    ]
    collector.on_step(transition, None, events)
    row = collector.end_episode(EpisodeSummary(1, None, 1, 0.0, False, None))
    assert row["need_switch_count"] == 2
