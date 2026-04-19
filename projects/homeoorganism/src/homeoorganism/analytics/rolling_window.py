"""Rolling window metrics for continuous lives."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from dataclasses import field

import numpy as np

from homeoorganism.analytics.metric_rows import WindowMetricRow
from homeoorganism.domain.types import BodyState


@dataclass
class RollingWindowMetrics:
    window_size: int
    life_id: int | None = None
    _energies: deque[int] = field(init=False)
    _waters: deque[int] = field(init=False)
    _energy_in_range_count: int = 0
    _water_in_range_count: int = 0
    _ticks_since_emit: int = 0

    def __post_init__(self) -> None:
        self._energies = deque(maxlen=self.window_size)
        self._waters = deque(maxlen=self.window_size)

    def begin_life(self, life_id: int) -> None:
        self.life_id = life_id
        self._energies.clear()
        self._waters.clear()
        self._energy_in_range_count = 0
        self._water_in_range_count = 0
        self._ticks_since_emit = 0

    def on_tick(self, tick: int, body: BodyState) -> WindowMetricRow | None:
        self._ticks_since_emit += 1
        self._drop_oldest_counts()
        self._append_body(body)
        if not self._ready_to_emit():
            return None
        self._ticks_since_emit = 0
        return self._build_row(tick)

    def current_ratios(self) -> tuple[float, float] | None:
        if len(self._energies) < self.window_size:
            return None
        return (
            self._energy_in_range_count / self.window_size,
            self._water_in_range_count / self.window_size,
        )

    def _drop_oldest_counts(self) -> None:
        if len(self._energies) < self.window_size:
            return
        self._energy_in_range_count -= int(20 <= self._energies[0] <= 90)
        self._water_in_range_count -= int(20 <= self._waters[0] <= 90)

    def _append_body(self, body: BodyState) -> None:
        self._energies.append(body.energy)
        self._waters.append(body.water)
        self._energy_in_range_count += int(20 <= body.energy <= 90)
        self._water_in_range_count += int(20 <= body.water <= 90)

    def _ready_to_emit(self) -> bool:
        if len(self._energies) < self.window_size:
            return False
        return self._ticks_since_emit >= self.window_size

    def _build_row(self, tick: int) -> WindowMetricRow:
        energy_ratio, water_ratio = self.current_ratios() or (0.0, 0.0)
        return WindowMetricRow(
            life_id=self.life_id or 0,
            tick=tick,
            window_size=self.window_size,
            energy_in_range_ratio=energy_ratio,
            water_in_range_ratio=water_ratio,
            deficit_variance=self._deficit_variance(),
        )

    def _deficit_variance(self) -> float:
        energy = np.array([(value - 70) / 70 for value in self._energies], dtype=float)
        water = np.array([(value - 70) / 70 for value in self._waters], dtype=float)
        return float(0.5 * np.var(energy) + 0.5 * np.var(water))
