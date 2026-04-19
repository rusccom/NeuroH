"""Row objects for RC4 continuous metrics."""

from dataclasses import dataclass
from dataclasses import field


@dataclass(frozen=True)
class WindowMetricRow:
    life_id: int
    tick: int
    window_size: int
    energy_in_range_ratio: float
    water_in_range_ratio: float
    deficit_variance: float


@dataclass(frozen=True)
class EventMetricRow:
    life_id: int
    tick: int
    event_type: str
    duration_ticks: int
    success: bool
    resource_type: str | None = None


@dataclass(frozen=True)
class LifeSummaryRow:
    life_id: int
    life_duration_ticks: int
    end_reason: str | None
    mode_entropy_by_state: dict[str, float] = field(default_factory=dict)
    mode_transition_coherence: float = 0.0
    mode_diversity: int = 0


@dataclass(frozen=True)
class SeriesBlockRow:
    block_index: int
    block_size: int
    start_life_id: int
    end_life_id: int
    survival_share: float
