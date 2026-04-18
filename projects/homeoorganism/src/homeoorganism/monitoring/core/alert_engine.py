"""Alert generation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from homeoorganism.v1_baseline.decision.status_translator import StatusTranslator
from homeoorganism.monitoring.domain.dto import OperatorEvent, StepSnapshot
from homeoorganism.monitoring.domain.enums import AlertLevel


@dataclass
class AlertEngine:
    translator: StatusTranslator
    _invalid_plan_steps: int = 0
    _positions: deque = field(default_factory=lambda: deque(maxlen=12))
    _collisions: deque = field(default_factory=lambda: deque(maxlen=10))
    _distances: deque = field(default_factory=lambda: deque(maxlen=8))

    def evaluate(self, snapshot: StepSnapshot) -> list[OperatorEvent]:
        self._positions.append(tuple(snapshot.world.pose[:2]))
        self._collisions.append(snapshot.body.last_collision)
        self._track_plan(snapshot)
        self._track_distance(snapshot)
        alerts = self._body_alerts(snapshot)
        alerts.extend(self._behavior_alerts(snapshot))
        return alerts

    def _body_alerts(self, snapshot: StepSnapshot) -> list[OperatorEvent]:
        alerts = []
        if snapshot.body.energy < 15:
            alerts.append(self._event(AlertLevel.CRITICAL, "LOW_ENERGY_CRITICAL", snapshot))
        elif snapshot.body.energy < 25:
            alerts.append(self._event(AlertLevel.WARN, "LOW_ENERGY_WARN", snapshot))
        if snapshot.body.water < 15:
            alerts.append(self._event(AlertLevel.CRITICAL, "LOW_WATER_CRITICAL", snapshot))
        elif snapshot.body.water < 25:
            alerts.append(self._event(AlertLevel.WARN, "LOW_WATER_WARN", snapshot))
        return alerts

    def _behavior_alerts(self, snapshot: StepSnapshot) -> list[OperatorEvent]:
        alerts = []
        if self._invalid_plan_steps > 5:
            alerts.append(self._event(AlertLevel.WARN, "NO_VALID_PLAN", snapshot))
        if len(set(self._positions)) <= 2 and len(self._positions) == self._positions.maxlen:
            alerts.append(self._event(AlertLevel.WARN, "STUCK_LOOP", snapshot))
        if sum(1 for item in self._collisions if item) >= 3:
            alerts.append(self._event(AlertLevel.WARN, "REPEATED_COLLISIONS", snapshot))
        if self._no_progress():
            alerts.append(self._event(AlertLevel.WARN, "NO_PROGRESS_TO_TARGET", snapshot))
        if snapshot.memory.fast_confidence > 0.5 and snapshot.memory.slow_confidence > 0.5:
            alerts.append(self._event(AlertLevel.INFO, "MEMORY_CONFLICT", snapshot))
        return alerts

    def _track_plan(self, snapshot: StepSnapshot) -> None:
        if snapshot.planner.plan_valid:
            self._invalid_plan_steps = 0
            return
        self._invalid_plan_steps += 1

    def _track_distance(self, snapshot: StepSnapshot) -> None:
        if snapshot.world.target is None:
            self._distances.clear()
            return
        x, y = snapshot.world.pose[:2]
        tx, ty = snapshot.world.target
        self._distances.append(abs(tx - x) + abs(ty - y))

    def _no_progress(self) -> bool:
        if len(self._distances) < self._distances.maxlen:
            return False
        return self._distances[-1] >= min(self._distances)

    def _event(self, level: AlertLevel, code: str, snapshot: StepSnapshot) -> OperatorEvent:
        return OperatorEvent(
            level=level,
            code=code,
            message=self.translator.alert_message(code),
            step_idx=snapshot.world.step_idx,
            ts_ms=snapshot.ts_ms,
        )
