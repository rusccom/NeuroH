"""Life-end metrics for continuous runs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from math import log2

from homeoorganism.analytics.metric_rows import LifeSummaryRow
from homeoorganism.analytics.state_categorizer import classify_state
from homeoorganism.domain.enums import EventType
from homeoorganism.domain.types import BodyState
from homeoorganism.domain.types import TargetProposal


@dataclass
class LifetimeMetrics:
    life_id: int | None = None
    _total_ticks: int = 0
    _state_mode_counts: dict[str, Counter[str]] = field(default_factory=dict)
    _mode_counts: Counter[str] = field(default_factory=Counter)
    _mode_max_dwell: dict[str, int] = field(default_factory=dict)
    _prev_mode: str | None = None
    _prev_state: str | None = None
    _current_dwell: int = 0
    _last_anchor_tick: int | None = None
    _transition_count: int = 0
    _coherent_transition_count: int = 0

    def begin_life(self, life_id: int) -> None:
        self.life_id = life_id
        self._total_ticks = 0
        self._state_mode_counts = {state: Counter() for state in self._states()}
        self._mode_counts.clear()
        self._mode_max_dwell.clear()
        self._prev_mode = None
        self._prev_state = None
        self._current_dwell = 0
        self._last_anchor_tick = None
        self._transition_count = 0
        self._coherent_transition_count = 0

    def on_tick(
        self,
        tick: int,
        body: BodyState,
        proposal: TargetProposal | None,
        anchor_events: tuple[EventType, ...] = (),
    ) -> None:
        state = classify_state(body)
        mode = behavior_mode(proposal)
        self._total_ticks += 1
        self._record_state_mode(state, mode)
        self._record_transition(tick, state, mode, anchor_events)
        self._record_dwell(mode)
        self._prev_mode = mode
        self._prev_state = state

    def finalize(self, life_duration_ticks: int, end_reason: str | None) -> LifeSummaryRow:
        self._commit_dwell()
        return LifeSummaryRow(
            life_id=self.life_id or 0,
            life_duration_ticks=life_duration_ticks,
            end_reason=end_reason,
            mode_entropy_by_state=self._entropies(),
            mode_transition_coherence=self._coherence(),
            mode_diversity=self._mode_diversity(),
        )

    def _record_state_mode(self, state: str, mode: str) -> None:
        self._state_mode_counts[state][mode] += 1
        self._mode_counts[mode] += 1

    def _record_transition(
        self,
        tick: int,
        state: str,
        mode: str,
        anchor_events: tuple[EventType, ...],
    ) -> None:
        anchor_now = self._has_anchor(anchor_events)
        if self._prev_mode is not None and mode != self._prev_mode:
            self._transition_count += 1
            if self._is_coherent(tick, state, anchor_now):
                self._coherent_transition_count += 1
        if anchor_now:
            self._last_anchor_tick = tick

    def _has_anchor(self, anchor_events: tuple[EventType, ...]) -> bool:
        anchor_set = {
            EventType.NEED_SWITCH,
            EventType.RESOURCE_OBSERVED,
            EventType.RESOURCE_CONSUMED,
            EventType.RESOURCE_RELOCATED,
            EventType.COLLISION,
        }
        return any(event in anchor_set for event in anchor_events)

    def _is_coherent(self, tick: int, state: str, anchor_now: bool) -> bool:
        if self._prev_state != state:
            return True
        if anchor_now:
            return True
        if self._last_anchor_tick is None:
            return False
        return tick - self._last_anchor_tick <= 3

    def _record_dwell(self, mode: str) -> None:
        if self._prev_mode == mode:
            self._current_dwell += 1
            return
        self._commit_dwell()
        self._current_dwell = 1

    def _commit_dwell(self) -> None:
        if self._prev_mode is None:
            return
        previous = self._mode_max_dwell.get(self._prev_mode, 0)
        self._mode_max_dwell[self._prev_mode] = max(previous, self._current_dwell)

    def _entropies(self) -> dict[str, float]:
        return {state: self._entropy(self._state_mode_counts[state]) for state in self._states()}

    def _entropy(self, counts: Counter[str]) -> float:
        total = sum(counts.values())
        if total == 0:
            return 0.0
        return -sum((count / total) * log2(count / total) for count in counts.values())

    def _coherence(self) -> float:
        if self._transition_count == 0:
            return 1.0
        return self._coherent_transition_count / self._transition_count

    def _mode_diversity(self) -> int:
        if self._total_ticks == 0:
            return 0
        return sum(1 for mode, count in self._mode_counts.items() if self._counts_for_diversity(mode, count))

    def _counts_for_diversity(self, mode: str, count: int) -> bool:
        if count / self._total_ticks < 0.02:
            return False
        return self._mode_max_dwell.get(mode, 0) >= 5

    def _states(self) -> tuple[str, ...]:
        return ("critical", "energy_dominant", "water_dominant", "neutral")


def behavior_mode(proposal: TargetProposal | None) -> str:
    if proposal is None:
        return "none:none"
    return f"{proposal.source.value}:{proposal.execution_mode.value}"
