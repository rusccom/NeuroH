"""Full-vs-ablation comparisons."""

from __future__ import annotations

from collections import defaultdict
from statistics import fmean


COMPARISON_FIELDS = (
    "input_name",
    "phase",
    "baseline_mode",
    "compared_mode",
    "metric",
    "direction",
    "baseline_value",
    "compared_value",
    "delta",
    "preferred_mode",
    "significance",
)

METRIC_DIRECTION = {
    "survival_steps_mean": "higher",
    "steps_to_first_needed_resource_mean": "lower",
    "return_steps_to_seen_resource_mean": "lower",
    "post_relocation_life_mean": "higher",
    "relocation_recovery_success_rate": "higher",
    "relocation_recovery_steps_mean": "lower",
    "mean_energy_deficit": "lower",
    "mean_water_deficit": "lower",
    "need_switch_count_mean": "lower",
    "stuck_windows_mean": "lower",
    "source_fast_share": "higher",
    "source_slow_share": "higher",
    "source_explore_share": "higher",
}


def build_comparison_rows(summary_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = group_phase_mode(summary_rows)
    rows: list[dict[str, object]] = []
    scopes = sorted({(str(row["input_name"]), str(row["phase"])) for row in summary_rows})
    for input_name, phase in scopes:
        rows.extend(phase_comparisons(grouped, input_name, phase))
    return rows


def group_phase_mode(
    summary_rows: list[dict[str, object]],
) -> dict[tuple[str, str, str], list[dict[str, object]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in summary_rows:
        key = (str(row["input_name"]), str(row["phase"]), str(row["mode"]))
        grouped[key].append(row)
    return grouped


def phase_comparisons(
    grouped: dict[tuple[str, str, str], list[dict[str, object]]],
    input_name: str,
    phase: str,
) -> list[dict[str, object]]:
    full_bucket = grouped.get((input_name, phase, "full"))
    if full_bucket is None:
        return []
    rows: list[dict[str, object]] = []
    compared_modes = sorted(
        mode
        for scope_input, phase_name, mode in grouped
        if scope_input == input_name and phase_name == phase and mode != "full"
    )
    for mode in compared_modes:
        rows.extend(metric_comparisons(input_name, phase, full_bucket, grouped[(input_name, phase, mode)], mode))
    return rows


def metric_comparisons(
    input_name: str,
    phase: str,
    full_bucket: list[dict[str, object]],
    compared_bucket: list[dict[str, object]],
    compared_mode: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for metric, direction in METRIC_DIRECTION.items():
        rows.append(
            build_comparison_row(input_name, phase, full_bucket, compared_bucket, compared_mode, metric, direction)
        )
    return rows


def build_comparison_row(
    input_name: str,
    phase: str,
    full_bucket: list[dict[str, object]],
    compared_bucket: list[dict[str, object]],
    compared_mode: str,
    metric: str,
    direction: str,
) -> dict[str, object]:
    baseline_value = bucket_mean(full_bucket, metric)
    compared_value = bucket_mean(compared_bucket, metric)
    return {
        "input_name": input_name,
        "phase": phase,
        "baseline_mode": "full",
        "compared_mode": compared_mode,
        "metric": metric,
        "direction": direction,
        "baseline_value": baseline_value,
        "compared_value": compared_value,
        "delta": difference(baseline_value, compared_value),
        "preferred_mode": preferred_mode(direction, baseline_value, compared_value, compared_mode),
        "significance": "not_computed",
    }


def bucket_mean(bucket: list[dict[str, object]], metric: str) -> float | None:
    values = [value for value in (to_float(row.get(metric)) for row in bucket) if value is not None]
    return None if not values else fmean(values)


def difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def preferred_mode(
    direction: str,
    baseline_value: float | None,
    compared_value: float | None,
    compared_mode: str,
) -> str | None:
    if baseline_value is None or compared_value is None:
        return None
    full_wins = baseline_value > compared_value if direction == "higher" else baseline_value < compared_value
    if baseline_value == compared_value:
        return None
    return "full" if full_wins else compared_mode


def to_float(value: object) -> float | None:
    if value in (None, "", "None"):
        return None
    return float(value)
