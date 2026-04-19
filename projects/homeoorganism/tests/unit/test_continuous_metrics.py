from homeoorganism.analytics.windowed_metrics import ContinuousMetrics
from homeoorganism.domain.enums import EventType
from homeoorganism.domain.enums import ExecutionMode
from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.enums import TargetSource
from homeoorganism.domain.types import BodyState
from homeoorganism.domain.types import TargetProposal


def test_continuous_metrics_emits_window_rows():
    metrics = ContinuousMetrics(window_sizes=(100,), block_size=5)
    metrics.begin_life(1)
    for tick in range(1, 100):
        window_rows, event_rows = metrics.on_tick(tick, BodyState(70, 70, False, True), _proposal(), None, ())
        assert window_rows == []
        assert event_rows == []
    window_rows, _ = metrics.on_tick(100, BodyState(70, 70, False, True), _proposal(), None, ())
    assert len(window_rows) == 1
    assert window_rows[0].window_size == 100


def test_continuous_metrics_life_end_returns_summary_and_series():
    metrics = ContinuousMetrics(window_sizes=(100,), block_size=5)
    for life_id in range(1, 6):
        metrics.begin_life(life_id)
        for tick in range(1, 101):
            metrics.on_tick(tick, BodyState(70, 70, False, True), _proposal(), None, ())
        summary, event_rows, series_row = metrics.on_life_end(4500, None)
        assert summary.life_id == life_id
        assert event_rows == []
    assert series_row is not None
    assert series_row.block_index == 1


def test_continuous_metrics_routes_shift_events():
    metrics = ContinuousMetrics(window_sizes=(100,), block_size=5)
    metrics.begin_life(1)
    for tick in range(1, 101):
        metrics.on_tick(tick, BodyState(70, 70, False, True), _proposal(), None, ())
    _, rows = metrics.on_tick(
        101,
        BodyState(40, 70, False, True),
        _proposal(),
        None,
        (EventType.RESOURCE_RELOCATED,),
    )
    assert rows == []
    _, rows = metrics.on_tick(102, BodyState(40, 70, False, True), _proposal(), ResourceType.FOOD, ())
    assert len(rows) == 1
    assert rows[0].event_type == "post_shift_recovery_ticks"


def _proposal() -> TargetProposal:
    return TargetProposal(
        TargetSource.FAST,
        ResourceType.FOOD,
        1.0,
        execution_mode=ExecutionMode.DIRECT,
    )
