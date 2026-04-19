"""Event-triggered metrics for continuous lives."""

from __future__ import annotations

from dataclasses import dataclass

from homeoorganism.analytics.metric_rows import EventMetricRow
from homeoorganism.analytics.state_categorizer import LOW_THRESHOLD
from homeoorganism.analytics.state_categorizer import dominant_resource
from homeoorganism.domain.enums import EventType
from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.types import BodyState
from homeoorganism.domain.types import TargetProposal


@dataclass
class EventMetrics:
    life_id: int | None = None
    _prev_body: BodyState | None = None
    _pending_low_tick: int | None = None
    _pending_low_resource: ResourceType | None = None
    _pending_directed_tick: int | None = None
    _pending_shift_tick: int | None = None
    _shift_consumed: bool = False

    def begin_life(self, life_id: int) -> None:
        self.life_id = life_id
        self._prev_body = None
        self._pending_low_tick = None
        self._pending_low_resource = None
        self._pending_directed_tick = None
        self._pending_shift_tick = None
        self._shift_consumed = False

    def on_tick(
        self,
        tick: int,
        body: BodyState,
        proposal: TargetProposal | None,
        consumed_resource: ResourceType | None,
        current_ratios: tuple[float, float] | None,
        anchor_events: tuple[EventType, ...] = (),
    ) -> list[EventMetricRow]:
        rows = self._start_shift_if_needed(tick, anchor_events)
        self._maybe_start_low_event(tick, body)
        self._append_row(rows, self._maybe_close_low_event(tick, proposal))
        self._append_row(rows, self._maybe_close_shift_event(tick, body, consumed_resource, current_ratios))
        self._prev_body = body
        return rows

    def flush(self, life_duration_ticks: int) -> list[EventMetricRow]:
        rows = []
        self._append_row(rows, self._flush_low_event(life_duration_ticks))
        self._append_row(rows, self._flush_shift_event(life_duration_ticks))
        return rows

    def _start_shift_if_needed(
        self,
        tick: int,
        anchor_events: tuple[EventType, ...],
    ) -> list[EventMetricRow]:
        if EventType.RESOURCE_RELOCATED not in anchor_events:
            return []
        rows = []
        self._append_row(rows, self._flush_shift_event(tick))
        self._pending_shift_tick = tick
        self._shift_consumed = False
        return rows

    def _maybe_start_low_event(self, tick: int, body: BodyState) -> None:
        if self._pending_low_tick is not None:
            return
        resource = self._crossed_low_resource(body)
        if resource is None:
            return
        self._pending_low_tick = tick
        self._pending_low_resource = resource
        self._pending_directed_tick = None

    def _crossed_low_resource(self, body: BodyState) -> ResourceType | None:
        if self._prev_body is None:
            return None
        resource = dominant_resource(body)
        prev_value = self._resource_value(self._prev_body, resource)
        current_value = self._resource_value(body, resource)
        if prev_value >= LOW_THRESHOLD and current_value < LOW_THRESHOLD:
            return resource
        return None

    def _maybe_close_low_event(
        self,
        tick: int,
        proposal: TargetProposal | None,
    ) -> EventMetricRow | None:
        if self._pending_low_tick is None or self._pending_low_resource is None:
            return None
        if self._directed_resource(proposal) != self._pending_low_resource:
            self._pending_directed_tick = None
            return None
        if self._pending_directed_tick is None:
            self._pending_directed_tick = tick
            return None
        return self._close_low_success()

    def _close_low_success(self) -> EventMetricRow:
        directed_tick = self._pending_directed_tick or 0
        start_tick = self._pending_low_tick or directed_tick
        resource = self._pending_low_resource.value if self._pending_low_resource else None
        row = EventMetricRow(
            life_id=self.life_id or 0,
            tick=directed_tick,
            event_type="anticipatory_response_time",
            duration_ticks=directed_tick - start_tick,
            success=True,
            resource_type=resource,
        )
        self._pending_low_tick = None
        self._pending_low_resource = None
        self._pending_directed_tick = None
        return row

    def _maybe_close_shift_event(
        self,
        tick: int,
        body: BodyState,
        consumed_resource: ResourceType | None,
        current_ratios: tuple[float, float] | None,
    ) -> EventMetricRow | None:
        if self._pending_shift_tick is None:
            return None
        if consumed_resource == dominant_resource(body):
            self._shift_consumed = True
        if not self._shift_consumed or not self._ratios_recovered(current_ratios):
            return None
        return self._close_shift_row(tick, True)

    def _ratios_recovered(self, current_ratios: tuple[float, float] | None) -> bool:
        if current_ratios is None:
            return False
        energy_ratio, water_ratio = current_ratios
        return energy_ratio >= 0.65 and water_ratio >= 0.65

    def _flush_low_event(self, tick: int) -> EventMetricRow | None:
        if self._pending_low_tick is None or self._pending_low_resource is None:
            return None
        row = EventMetricRow(
            life_id=self.life_id or 0,
            tick=tick,
            event_type="anticipatory_response_time",
            duration_ticks=tick - self._pending_low_tick,
            success=False,
            resource_type=self._pending_low_resource.value,
        )
        self._pending_low_tick = None
        self._pending_low_resource = None
        self._pending_directed_tick = None
        return row

    def _flush_shift_event(self, tick: int) -> EventMetricRow | None:
        if self._pending_shift_tick is None:
            return None
        return self._close_shift_row(tick, False)

    def _close_shift_row(self, tick: int, success: bool) -> EventMetricRow:
        start_tick = self._pending_shift_tick or tick
        row = EventMetricRow(
            life_id=self.life_id or 0,
            tick=tick,
            event_type="post_shift_recovery_ticks",
            duration_ticks=tick - start_tick,
            success=success,
        )
        self._pending_shift_tick = None
        self._shift_consumed = False
        return row

    def _resource_value(self, body: BodyState, resource: ResourceType) -> int:
        if resource == ResourceType.FOOD:
            return body.energy
        return body.water

    def _directed_resource(self, proposal: TargetProposal | None) -> ResourceType | None:
        if proposal is None:
            return None
        return proposal.resource_type

    def _append_row(self, rows: list[EventMetricRow], row: EventMetricRow | None) -> None:
        if row is not None:
            rows.append(row)
