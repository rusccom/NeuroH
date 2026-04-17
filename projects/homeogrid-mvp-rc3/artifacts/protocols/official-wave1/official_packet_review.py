from __future__ import annotations

from pathlib import Path

from official_packet_core import METRICS, episode_id, monitoring_file, none_high, safe, value


def replay_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    specs = (
        ("full_strong", "highest_survival"),
        ("full_relocation", "best_recovery"),
        ("no_fast_relocation", "weak_recovery"),
        ("no_slow_train", "slow_memory_gap"),
        ("no_interoception_train", "high_deficit_low_switch"),
    )
    selected: list[dict[str, object]] = []
    for category, rule in specs:
        candidates = sorted(case_candidates(rows, category), key=lambda row: sort_key(category, row))
        selected.extend(top_case_rows(category, rule, candidates))
    return selected


def top_case_rows(category: str, rule: str, candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for slot, row in enumerate(candidates[:2], start=1):
        rows.append(replay_case_row(category, rule, slot, row))
    return rows


def case_candidates(rows: list[dict[str, object]], category: str) -> list[dict[str, object]]:
    if category == "full_strong":
        return [row for row in rows if row["mode"] == "full" and row["phase"] == "train"]
    if category == "full_relocation":
        return [row for row in rows if row["mode"] == "full" and row["phase"] == "eval_relocation"]
    if category == "no_fast_relocation":
        return [row for row in rows if row["mode"] == "no_fast" and row["phase"] == "eval_relocation"]
    if category == "no_slow_train":
        return [row for row in rows if row["mode"] == "no_slow" and row["phase"] == "train"]
    return [row for row in rows if row["mode"] == "no_interoception" and row["phase"] == "train"]


def sort_key(category: str, row: dict[str, object]) -> tuple[object, ...]:
    if category == "full_strong":
        return (-safe(row, "survival_steps"), -safe(row, "total_reward"), row["launch_seed"], episode_id(row))
    if category == "full_relocation":
        return (-safe(row, "relocation_recovery_success_rate"), none_high(row, "relocation_recovery_steps"), -safe(row, "post_relocation_life"), row["launch_seed"], episode_id(row))
    if category == "no_fast_relocation":
        return (none_high(row, "post_relocation_life"), safe(row, "survival_steps"), row["launch_seed"], episode_id(row))
    if category == "no_slow_train":
        return (-safe(row, "steps_to_first_needed_resource"), -safe(row, "return_steps_to_seen_resource"), row["launch_seed"], episode_id(row))
    return (-safe(row, "mean_water_deficit"), safe(row, "need_switch_count"), safe(row, "survival_steps"), row["launch_seed"], episode_id(row))


def replay_case_row(
    category: str,
    rule: str,
    slot: int,
    row: dict[str, object],
) -> dict[str, object]:
    file_path = monitoring_file(row)
    record_count, alert_count = monitoring_counts(file_path)
    payload = {
        "category": category,
        "slot": slot,
        "selection_rule": rule,
        "mode": row["mode"],
        "seed": row["launch_seed"],
        "phase": row["phase"],
        "episode_id": episode_id(row),
        "survival_steps": value(row, "survival_steps"),
        "record_count": record_count,
        "alert_count": alert_count,
        "monitoring_file": str(file_path),
    }
    for metric in METRICS:
        if metric != "survival_steps":
            payload[metric] = value(row, metric)
    return payload


def monitoring_counts(path: Path) -> tuple[int, int]:
    record_count = 0
    alert_count = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        record_count += 1
        if '"type": "alert"' in raw_line:
            alert_count += 1
    return record_count, alert_count


def review_payload(
    rows: list[dict[str, object]],
    phase_rows: list[dict[str, object]],
    replay_path: Path,
) -> dict[str, object]:
    lookup = {(row["mode"], row["phase"]): row for row in phase_rows}
    comparisons = [comparison(lookup, *spec) for spec in comparison_specs()]
    return {
        "run_count": len({(row["mode"], row["launch_seed"]) for row in rows}),
        "episode_count": len(rows),
        "comparisons": comparisons,
        "interoception_signals": interoception_rows(lookup),
        "source_checks_train": source_checks(lookup),
        "source_check_status": source_status(lookup),
        "relocation_overview": relocation_overview(lookup),
        "replay_cases_path": str(replay_path),
    }


def comparison_specs() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("train", "no_slow", "steps_to_first_needed_resource", "lower"),
        ("eval_seen", "no_fast", "return_steps_to_seen_resource", "lower"),
        ("eval_relocation", "no_fast", "return_steps_to_seen_resource", "lower"),
        ("eval_relocation", "no_fast", "relocation_recovery_success_rate", "higher"),
        ("eval_relocation", "no_fast", "relocation_recovery_steps", "lower"),
        ("train", "no_interoception", "survival_steps", "higher"),
        ("eval_seen", "no_interoception", "survival_steps", "higher"),
        ("eval_relocation", "no_interoception", "survival_steps", "higher"),
    )


def comparison(
    lookup: dict[tuple[str, str], dict[str, object]],
    phase: str,
    baseline_mode: str,
    metric: str,
    direction: str,
) -> dict[str, object]:
    full_value = value(lookup[("full", phase)], metric)
    baseline_value = value(lookup[(baseline_mode, phase)], metric)
    improvement, status = comparison_status(full_value, baseline_value, direction)
    return {
        "phase": phase,
        "baseline_mode": baseline_mode,
        "metric": metric,
        "direction": direction,
        "full_value": full_value,
        "baseline_value": baseline_value,
        "improvement": improvement,
        "status": status,
    }


def comparison_status(
    full_value: float | None,
    baseline_value: float | None,
    direction: str,
) -> tuple[float | None, str]:
    if full_value is None or baseline_value is None:
        return None, "missing_metric"
    if baseline_value == 0:
        return None, "baseline_zero"
    delta = full_value - baseline_value
    improvement = delta / baseline_value if direction == "higher" else -delta / baseline_value
    return improvement, "pass" if improvement > 0 else "fail"


def interoception_rows(
    lookup: dict[tuple[str, str], dict[str, object]],
) -> list[dict[str, object]]:
    phases = ("train", "eval_seen", "eval_relocation")
    return [interoception_row(lookup, phase) for phase in phases]


def interoception_row(
    lookup: dict[tuple[str, str], dict[str, object]],
    phase: str,
) -> dict[str, object]:
    full_row = lookup[("full", phase)]
    baseline = lookup[("no_interoception", phase)]
    return {
        "phase": phase,
        "full_need_switch_count": value(full_row, "need_switch_count"),
        "no_interoception_need_switch_count": value(baseline, "need_switch_count"),
        "full_mean_energy_deficit": value(full_row, "mean_energy_deficit"),
        "no_interoception_mean_energy_deficit": value(baseline, "mean_energy_deficit"),
        "full_mean_water_deficit": value(full_row, "mean_water_deficit"),
        "no_interoception_mean_water_deficit": value(baseline, "mean_water_deficit"),
    }


def source_checks(
    lookup: dict[tuple[str, str], dict[str, object]],
) -> dict[str, dict[str, float | None]]:
    modes = ("full", "no_fast", "no_slow", "no_interoception")
    return {mode: source_row(lookup[(mode, "train")]) for mode in modes}


def source_row(row: dict[str, object]) -> dict[str, float | None]:
    metrics = ("source_fast_share", "source_slow_share", "source_explore_share")
    return {metric: value(row, metric) for metric in metrics}


def source_status(lookup: dict[tuple[str, str], dict[str, object]]) -> dict[str, bool]:
    return {
        "full_slow_gt_zero": (value(lookup[("full", "train")], "source_slow_share") or 0.0) > 0.0,
        "no_slow_slow_near_zero": (value(lookup[("no_slow", "train")], "source_slow_share") or 0.0) <= 1e-9,
        "no_fast_fast_near_zero": (value(lookup[("no_fast", "train")], "source_fast_share") or 0.0) <= 1e-9,
    }


def relocation_overview(
    lookup: dict[tuple[str, str], dict[str, object]],
) -> dict[str, dict[str, float | None]]:
    modes = ("full", "no_fast", "no_slow", "no_interoception")
    metrics = ("relocation_recovery_success_rate", "relocation_recovery_steps", "post_relocation_life", "survival_steps")
    return {mode: {metric: value(lookup[(mode, "eval_relocation")], metric) for metric in metrics} for mode in modes}
