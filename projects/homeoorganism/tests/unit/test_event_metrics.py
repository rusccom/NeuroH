from homeoorganism.analytics.event_metrics import EventMetrics
from homeoorganism.domain.enums import EventType
from homeoorganism.domain.enums import ExecutionMode
from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.enums import TargetSource
from homeoorganism.domain.types import BodyState
from homeoorganism.domain.types import TargetProposal


def test_anticipatory_response_triggers_on_low_crossing():
    metrics = EventMetrics()
    metrics.begin_life(1)
    metrics.on_tick(1, BodyState(20, 70, False, True), None, None, None)
    metrics.on_tick(2, BodyState(14, 70, False, True), None, None, None)
    metrics.on_tick(3, BodyState(14, 70, False, True), _proposal(ResourceType.FOOD), None, None)
    rows = metrics.on_tick(4, BodyState(14, 70, False, True), _proposal(ResourceType.FOOD), None, None)
    assert len(rows) == 1
    assert rows[0].event_type == "anticipatory_response_time"
    assert rows[0].duration_ticks == 1


def test_post_shift_recovery_requires_consumption_and_ratios():
    metrics = EventMetrics()
    metrics.begin_life(1)
    rows = metrics.on_tick(
        10,
        BodyState(40, 40, False, True),
        None,
        None,
        (0.8, 0.8),
        (EventType.RESOURCE_RELOCATED,),
    )
    assert rows == []
    rows = metrics.on_tick(11, BodyState(40, 40, False, True), None, ResourceType.FOOD, (0.5, 0.8))
    assert rows == []


def test_post_shift_recovery_success():
    metrics = EventMetrics()
    metrics.begin_life(1)
    metrics.on_tick(10, BodyState(40, 40, False, True), None, None, (0.8, 0.8), (EventType.RESOURCE_RELOCATED,))
    rows = metrics.on_tick(12, BodyState(40, 60, False, True), None, ResourceType.FOOD, (0.7, 0.7))
    assert len(rows) == 1
    assert rows[0].event_type == "post_shift_recovery_ticks"
    assert rows[0].duration_ticks == 2
    assert rows[0].success is True


def _proposal(resource_type: ResourceType) -> TargetProposal:
    return TargetProposal(TargetSource.FAST, resource_type, 1.0, execution_mode=ExecutionMode.DIRECT)
