from homeoorganism.analytics.lifetime_metrics import LifetimeMetrics
from homeoorganism.domain.enums import EventType
from homeoorganism.domain.enums import ExecutionMode
from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.enums import TargetSource
from homeoorganism.domain.types import BodyState
from homeoorganism.domain.types import TargetProposal


def test_mode_entropy_nonuniform():
    metrics = LifetimeMetrics()
    metrics.begin_life(1)
    for tick in range(1, 9):
        metrics.on_tick(tick, BodyState(70, 70, False, True), _proposal(TargetSource.FAST), ())
    for tick in range(9, 11):
        metrics.on_tick(tick, BodyState(70, 70, False, True), _proposal(TargetSource.SLOW), ())
    row = metrics.finalize(10, None)
    assert row.mode_entropy_by_state["neutral"] < 1.0


def test_mode_transition_coherence_event_anchored():
    metrics = LifetimeMetrics()
    metrics.begin_life(1)
    metrics.on_tick(1, BodyState(70, 70, False, True), _proposal(TargetSource.FAST), ())
    metrics.on_tick(2, BodyState(70, 70, False, True), _proposal(TargetSource.SLOW), (EventType.COLLISION,))
    row = metrics.finalize(2, None)
    assert row.mode_transition_coherence == 1.0


def test_mode_diversity_threshold():
    metrics = LifetimeMetrics()
    metrics.begin_life(1)
    for tick in range(1, 96):
        metrics.on_tick(tick, BodyState(70, 70, False, True), _proposal(TargetSource.FAST), ())
    for tick in range(96, 99):
        metrics.on_tick(tick, BodyState(70, 70, False, True), _proposal(TargetSource.SLOW), ())
    metrics.on_tick(99, BodyState(70, 70, False, True), None, ())
    metrics.on_tick(100, BodyState(70, 70, False, True), None, ())
    row = metrics.finalize(100, None)
    assert row.mode_diversity == 1


def _proposal(source: TargetSource) -> TargetProposal:
    return TargetProposal(source, ResourceType.FOOD, 1.0, execution_mode=ExecutionMode.DIRECT)
