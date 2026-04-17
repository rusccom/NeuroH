"""Summary table assembly."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import fmean, pstdev


SUMMARY_FIELDS = (
    "input_name",
    "run_id",
    "mode",
    "phase",
    "seed",
    "config_hash",
    "episode_count",
    "biome_distribution",
    "survival_steps_mean",
    "survival_steps_std",
    "steps_to_first_needed_resource_mean",
    "return_steps_to_seen_resource_mean",
    "post_relocation_life_mean",
    "relocation_recovery_success_rate",
    "relocation_recovery_steps_mean",
    "mean_energy_deficit",
    "mean_water_deficit",
    "need_switch_count_mean",
    "stuck_windows_mean",
    "source_fast_share",
    "source_slow_share",
    "source_explore_share",
)

FIELD_TO_METRIC = {
    "survival_steps_mean": "survival_steps",
    "steps_to_first_needed_resource_mean": "steps_to_first_needed_resource",
    "return_steps_to_seen_resource_mean": "return_steps_to_seen_resource",
    "post_relocation_life_mean": "post_relocation_life",
    "relocation_recovery_success_rate": "relocation_recovery_success_rate",
    "relocation_recovery_steps_mean": "relocation_recovery_steps",
    "mean_energy_deficit": "mean_energy_deficit",
    "mean_water_deficit": "mean_water_deficit",
    "need_switch_count_mean": "need_switch_count",
    "stuck_windows_mean": "stuck_windows",
    "source_fast_share": "source_fast_share",
    "source_slow_share": "source_slow_share",
    "source_explore_share": "source_explore_share",
}


def build_summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = group_rows(rows)
    return [build_summary_row(key, bucket) for key, bucket in sorted(grouped.items())]


def group_rows(rows: list[dict[str, object]]) -> dict[tuple[object, ...], list[dict[str, object]]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (
            row["input_name"],
            row["run_id"],
            row["mode"],
            row["phase"],
            row["seed"],
            row["config_hash"],
        )
        grouped[key].append(row)
    return grouped


def build_summary_row(key: tuple[object, ...], bucket: list[dict[str, object]]) -> dict[str, object]:
    input_name, run_id, mode, phase, seed, config_hash = key
    row = {
        "input_name": input_name,
        "run_id": run_id,
        "mode": mode,
        "phase": phase,
        "seed": seed,
        "config_hash": config_hash,
        "episode_count": len(bucket),
        "biome_distribution": biome_distribution(bucket),
    }
    row.update(metric_columns(bucket))
    return row


def biome_distribution(bucket: list[dict[str, object]]) -> str:
    counts = Counter(str(row.get("biome_id", "unknown")) for row in bucket)
    return ",".join(f"{key}:{counts[key]}" for key in sorted(counts))


def metric_columns(bucket: list[dict[str, object]]) -> dict[str, object]:
    columns: dict[str, object] = {}
    for field, metric in FIELD_TO_METRIC.items():
        columns[field] = metric_mean(bucket, metric)
    columns["survival_steps_std"] = metric_std(bucket, "survival_steps")
    return columns


def metric_mean(bucket: list[dict[str, object]], metric: str) -> float | None:
    values = metric_values(bucket, metric)
    return None if not values else fmean(values)


def metric_std(bucket: list[dict[str, object]], metric: str) -> float | None:
    values = metric_values(bucket, metric)
    if not values:
        return None
    return 0.0 if len(values) == 1 else pstdev(values)


def metric_values(bucket: list[dict[str, object]], metric: str) -> list[float]:
    return [value for value in (to_float(row.get(metric)) for row in bucket) if value is not None]


def to_float(value: object) -> float | None:
    if value is None or value in ("", "None", "True", "False"):
        return None
    if isinstance(value, bool):
        return None
    return float(value)
