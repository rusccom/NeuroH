from homeoorganism.analytics.series_metrics import SeriesMetrics


def test_learning_curve_block_aggregation():
    metrics = SeriesMetrics()
    assert metrics.on_life_end(1, 3900) is None
    assert metrics.on_life_end(2, 4000) is None
    assert metrics.on_life_end(3, 5000) is None
    assert metrics.on_life_end(4, 2500) is None
    row = metrics.on_life_end(5, 4500)
    assert row is not None
    assert row.block_index == 1
    assert row.survival_share == 0.6
