from homeoorganism.analytics.rolling_window import RollingWindowMetrics
from homeoorganism.domain.types import BodyState


def test_rolling_window_emits_at_full_window():
    metrics = RollingWindowMetrics(100)
    metrics.begin_life(1)
    for tick in range(1, 100):
        assert metrics.on_tick(tick, BodyState(70, 70, False, True)) is None
    row = metrics.on_tick(100, BodyState(70, 70, False, True))
    assert row is not None
    assert row.tick == 100


def test_rolling_window_energy_in_range_count():
    metrics = RollingWindowMetrics(100)
    metrics.begin_life(1)
    for tick in range(1, 51):
        metrics.on_tick(tick, BodyState(70, 70, False, True))
    for tick in range(51, 100):
        metrics.on_tick(tick, BodyState(10, 10, False, True))
    row = metrics.on_tick(100, BodyState(10, 10, False, True))
    assert row is not None
    assert row.energy_in_range_ratio == 0.5
    assert row.water_in_range_ratio == 0.5


def test_deficit_variance_on_stable_state():
    metrics = RollingWindowMetrics(100)
    metrics.begin_life(1)
    for tick in range(1, 101):
        row = metrics.on_tick(tick, BodyState(70, 70, False, True))
    assert row is not None
    assert row.deficit_variance == 0.0
