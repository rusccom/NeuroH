from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import fmean, median, pstdev

METRICS = (
    "steps_to_first_needed_resource",
    "return_steps_to_seen_resource",
    "survival_steps",
    "relocation_recovery_success_rate",
    "relocation_recovery_steps",
    "post_relocation_life",
    "source_fast_share",
    "source_slow_share",
    "source_explore_share",
    "mean_energy_deficit",
    "mean_water_deficit",
    "need_switch_count",
    "stuck_windows",
    "total_reward",
)
RELOCATION_STEP = 45.0


def load_rows(output_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for manifest_path in sorted(output_dir.glob("*/*/seed_*/run_manifest.json")):
        rows.extend(load_run_rows(manifest_path.parent))
    return rows


def load_run_rows(run_root: Path) -> list[dict[str, object]]:
    manifest = json.loads((run_root / "run_manifest.json").read_text(encoding="utf-8"))
    metrics_path = run_root / "reports" / "metrics.csv"
    with metrics_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [enrich_row(row, manifest, run_root) for row in reader]


def enrich_row(row: dict[str, str], manifest: dict[str, object], run_root: Path) -> dict[str, object]:
    enriched: dict[str, object] = dict(row)
    enriched["launch_seed"] = int(manifest["base_seed"])
    enriched["run_root"] = str(run_root)
    enriched["post_relocation_life"] = post_relocation_life(row)
    return enriched


def post_relocation_life(row: dict[str, str]) -> float | None:
    survival = value(row, "survival_steps")
    if row.get("phase") != "eval_relocation" or survival is None:
        return None
    return survival - RELOCATION_STEP


def seed_mean_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = group_rows(rows, ("mode", "phase", "launch_seed"))
    metric_map: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    episode_counts: dict[tuple[str, str], int] = {}
    for (mode, phase, _seed), bucket in grouped.items():
        episode_counts[(mode, phase)] = len(bucket)
        for metric in METRICS:
            values = metric_values(bucket, metric)
            if values:
                metric_map[(mode, phase, metric)].append(fmean(values))
    return [seed_summary_row(key, metric_map[key], episode_counts) for key in sorted(metric_map)]


def seed_summary_row(
    key: tuple[str, str, str],
    values: list[float],
    episode_counts: dict[tuple[str, str], int],
) -> dict[str, object]:
    mode, phase, metric = key
    return {
        "mode": mode,
        "phase": phase,
        "metric": metric,
        "seed_count": len(values),
        "episode_count": episode_counts[(mode, phase)],
        "mean": fmean(values),
        "median": median(values),
        "std": 0.0 if len(values) == 1 else pstdev(values),
        "min": min(values),
        "max": max(values),
    }


def group_summary(rows: list[dict[str, object]], keys: tuple[str, ...]) -> list[dict[str, object]]:
    grouped = group_rows(rows, keys)
    return [group_summary_row(keys, key, bucket) for key, bucket in sorted(grouped.items())]


def group_summary_row(
    keys: tuple[str, ...],
    key: tuple[object, ...],
    bucket: list[dict[str, object]],
) -> dict[str, object]:
    seed_count = len({int(row["launch_seed"]) for row in bucket})
    summary = key_fields(keys, key)
    summary["episode_count"] = normalized_count(len(bucket), seed_count)
    summary["seed_count"] = seed_count
    for metric in METRICS:
        values = metric_values(bucket, metric)
        summary[metric] = fmean(values) if values else None
        summary[f"{metric}__non_null"] = normalized_count(len(values), seed_count)
    return summary


def coverage_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = group_rows(rows, ("mode", "phase"))
    coverage: list[dict[str, object]] = []
    for (mode, phase), bucket in sorted(grouped.items()):
        seed_count = len({int(row["launch_seed"]) for row in bucket})
        total = normalized_count(len(bucket), seed_count)
        for metric in METRICS:
            non_null = normalized_count(len(metric_values(bucket, metric)), seed_count)
            ratio = 0.0 if total == 0 else non_null / total
            coverage.append(coverage_row(mode, phase, metric, total, non_null, ratio))
    return coverage


def coverage_row(
    mode: str,
    phase: str,
    metric: str,
    total: int,
    non_null: int,
    ratio: float,
) -> dict[str, object]:
    return {
        "mode": mode,
        "phase": phase,
        "metric": metric,
        "episode_count": total,
        "non_null_count": non_null,
        "coverage_ratio": ratio,
    }


def group_rows(
    rows: list[dict[str, object]],
    keys: tuple[str, ...],
) -> dict[tuple[object, ...], list[dict[str, object]]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def metric_values(rows: list[dict[str, object]], metric: str) -> list[float]:
    return [item for item in (value(row, metric) for row in rows) if item is not None]


def key_fields(keys: tuple[str, ...], key: tuple[object, ...]) -> dict[str, object]:
    fields = dict(zip(keys, key, strict=True))
    if "launch_seed" in fields:
        fields["seed"] = fields.pop("launch_seed")
    return fields


def normalized_count(total: int, seed_count: int) -> int:
    if seed_count <= 1:
        return total
    return total // seed_count


def value(row: dict[str, object], key: str) -> float | None:
    raw = row.get(key)
    if raw in (None, "", "None"):
        return None
    return float(raw)


def safe(row: dict[str, object], key: str) -> float:
    return value(row, key) or 0.0


def none_high(row: dict[str, object], key: str) -> float:
    item = value(row, key)
    return 1e9 if item is None else item


def episode_id(row: dict[str, object]) -> int:
    return int(str(row["episode_id"]))


def monitoring_file(row: dict[str, object]) -> Path:
    run_root = Path(str(row["run_root"]))
    return run_root / "monitoring" / str(row["run_id"]) / f"{episode_id(row)}.jsonl"
