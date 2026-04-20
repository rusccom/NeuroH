"""Aggregate matrix summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean, median, pstdev


SUMMARY_METRICS = (
    "life_duration_ticks",
    "mode_transition_coherence",
    "mode_diversity",
    "steps_to_first_needed_resource",
    "return_steps_to_seen_resource",
    "survival_steps",
    "relocation_recovery_steps",
    "relocation_recovery_success_rate",
    "mean_energy_deficit",
    "mean_water_deficit",
    "source_fast_share",
    "source_slow_share",
    "source_explore_share",
)


@dataclass(frozen=True)
class MatrixSummaryBuilder:
    metrics: tuple[str, ...] = field(default_factory=lambda: SUMMARY_METRICS)

    def build(self, rows: list[dict[str, str]]) -> list[dict[str, float | int | str]]:
        grouped = self._group_seed_rows(rows)
        aggregated = self._aggregate_seed_means(grouped)
        return self._summary_rows(aggregated, grouped)

    def _group_seed_rows(self, rows: list[dict[str, str]]) -> dict[tuple[str, str, int], list[dict[str, str]]]:
        grouped: dict[tuple[str, str, int], list[dict[str, str]]] = {}
        for row in rows:
            key = (row["mode"], row["phase"], int(row["seed"]))
            grouped.setdefault(key, []).append(row)
        return grouped

    def _aggregate_seed_means(
        self,
        grouped: dict[tuple[str, str, int], list[dict[str, str]]],
    ) -> dict[tuple[str, str, str], list[float]]:
        aggregated: dict[tuple[str, str, str], list[float]] = {}
        for (mode, phase, _seed), rows in grouped.items():
            self._append_metric_means(aggregated, mode, phase, rows)
        return aggregated

    def _append_metric_means(
        self,
        aggregated: dict[tuple[str, str, str], list[float]],
        mode: str,
        phase: str,
        rows: list[dict[str, str]],
    ) -> None:
        for metric in self.metrics:
            values = [value for value in (self._to_float(row.get(metric)) for row in rows) if value is not None]
            if not values:
                continue
            aggregated.setdefault((mode, phase, metric), []).append(fmean(values))

    def _summary_rows(
        self,
        aggregated: dict[tuple[str, str, str], list[float]],
        grouped: dict[tuple[str, str, int], list[dict[str, str]]],
    ) -> list[dict[str, float | int | str]]:
        rows = []
        for key in sorted(aggregated):
            rows.append(self._summary_row(key, aggregated[key], grouped))
        return rows

    def _summary_row(
        self,
        key: tuple[str, str, str],
        values: list[float],
        grouped: dict[tuple[str, str, int], list[dict[str, str]]],
    ) -> dict[str, float | int | str]:
        mode, phase, metric = key
        episode_count = self._episode_count(mode, phase, grouped)
        return {
            "mode": mode,
            "phase": phase,
            "metric": metric,
            "seed_count": len(values),
            "episode_count": episode_count,
            "mean": fmean(values),
            "median": median(values),
            "std": 0.0 if len(values) == 1 else pstdev(values),
            "min": min(values),
            "max": max(values),
        }

    def _episode_count(
        self,
        mode: str,
        phase: str,
        grouped: dict[tuple[str, str, int], list[dict[str, str]]],
    ) -> int:
        return sum(len(rows) for (row_mode, row_phase, _), rows in grouped.items() if (row_mode, row_phase) == (mode, phase))

    def _to_float(self, raw: str | None) -> float | None:
        if raw in (None, ""):
            return None
        return float(raw)
