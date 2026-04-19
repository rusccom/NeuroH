"""Cross-life series metrics."""

from dataclasses import dataclass
from dataclasses import field

from homeoorganism.analytics.metric_rows import SeriesBlockRow


@dataclass
class SeriesMetrics:
    block_size: int = 5
    _block_index: int = 0
    _life_ids: list[int] = field(default_factory=list)
    _durations: list[int] = field(default_factory=list)

    def on_life_end(self, life_id: int, life_duration_ticks: int) -> SeriesBlockRow | None:
        self._life_ids.append(life_id)
        self._durations.append(life_duration_ticks)
        if len(self._durations) < self.block_size:
            return None
        return self._close_block()

    def _close_block(self) -> SeriesBlockRow:
        self._block_index += 1
        start_life = self._life_ids[0]
        end_life = self._life_ids[-1]
        survival_share = sum(duration >= 4000 for duration in self._durations) / self.block_size
        row = SeriesBlockRow(self._block_index, self.block_size, start_life, end_life, survival_share)
        self._life_ids.clear()
        self._durations.clear()
        return row
