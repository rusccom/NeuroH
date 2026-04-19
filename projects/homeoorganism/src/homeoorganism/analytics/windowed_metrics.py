"""Facade for RC4 continuous metrics."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from homeoorganism.analytics.event_metrics import EventMetrics
from homeoorganism.analytics.lifetime_metrics import LifetimeMetrics
from homeoorganism.analytics.metric_rows import EventMetricRow
from homeoorganism.analytics.metric_rows import LifeSummaryRow
from homeoorganism.analytics.metric_rows import SeriesBlockRow
from homeoorganism.analytics.metric_rows import WindowMetricRow
from homeoorganism.analytics.rolling_window import RollingWindowMetrics
from homeoorganism.analytics.series_metrics import SeriesMetrics
from homeoorganism.domain.enums import EventType
from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.types import BodyState
from homeoorganism.domain.types import TargetProposal


@dataclass
class ContinuousMetrics:
    window_sizes: tuple[int, ...] = (100, 500, 1000)
    block_size: int = 5
    events: EventMetrics = field(default_factory=EventMetrics)
    lifetime: LifetimeMetrics = field(default_factory=LifetimeMetrics)
    _life_id: int | None = None
    _rolling: dict[int, RollingWindowMetrics] = field(init=False)
    _series: SeriesMetrics = field(init=False)

    def __post_init__(self) -> None:
        self._rolling = {size: RollingWindowMetrics(size) for size in self.window_sizes}
        self._series = SeriesMetrics(self.block_size)

    def begin_life(self, life_id: int) -> None:
        self._life_id = life_id
        for collector in self._rolling.values():
            collector.begin_life(life_id)
        self.events.begin_life(life_id)
        self.lifetime.begin_life(life_id)

    def on_tick(
        self,
        tick: int,
        body: BodyState,
        proposal: TargetProposal | None,
        consumed_resource: ResourceType | None = None,
        anchor_events: tuple[EventType, ...] = (),
    ) -> tuple[list[WindowMetricRow], list[EventMetricRow]]:
        window_rows = [row for row in self._window_rows(tick, body) if row is not None]
        current_ratios = self._rolling[100].current_ratios() if 100 in self._rolling else None
        event_rows = self.events.on_tick(tick, body, proposal, consumed_resource, current_ratios, anchor_events)
        self.lifetime.on_tick(tick, body, proposal, anchor_events)
        return window_rows, event_rows

    def on_life_end(
        self,
        life_duration_ticks: int,
        end_reason: str | None,
    ) -> tuple[LifeSummaryRow, list[EventMetricRow], SeriesBlockRow | None]:
        summary = self.lifetime.finalize(life_duration_ticks, end_reason)
        event_rows = self.events.flush(life_duration_ticks)
        series_row = self._series.on_life_end(self._life_id or 0, life_duration_ticks)
        return summary, event_rows, series_row

    def _window_rows(self, tick: int, body: BodyState) -> list[WindowMetricRow | None]:
        return [self._rolling[size].on_tick(tick, body) for size in sorted(self._rolling)]
