"""Detected pathological result patterns for generated reports.

These flags describe symptoms for verdict documentation only.
Root-cause analysis stays outside release-tooling.
"""

from __future__ import annotations


def full_observation_pathology(summary_rows: list[dict[str, object]]) -> dict[str, object] | None:
    grouped = group_input_phase(summary_rows)
    for input_name in sorted({str(row["input_name"]) for row in summary_rows}):
        core_row = grouped.get((input_name, "core", "full_observation"))
        relocation_row = grouped.get((input_name, "relocation", "full_observation"))
        if core_row is None or relocation_row is None:
            continue
        if core_row.get("steps_to_first_needed_resource_mean") is not None:
            continue
        if relocation_row.get("steps_to_first_needed_resource_mean") is not None:
            continue
        if float(relocation_row.get("relocation_recovery_success_rate") or 0.0) != 0.0:
            continue
        full_row = grouped.get((input_name, "relocation", "full"))
        if full_row is None:
            continue
        if not lower_survival(relocation_row, full_row):
            continue
        return {
            "input_name": input_name,
            "relocation_survival": relocation_row.get("survival_steps_mean"),
            "full_relocation_survival": full_row.get("survival_steps_mean"),
            "relocation_recovery_success_rate": relocation_row.get("relocation_recovery_success_rate"),
        }
    return None


def group_input_phase(summary_rows: list[dict[str, object]]) -> dict[tuple[str, str, str], dict[str, object]]:
    return {
        (str(row["input_name"]), str(row["phase"]), str(row["mode"])): row
        for row in summary_rows
    }


def lower_survival(pathology_row: dict[str, object], full_row: dict[str, object]) -> bool:
    pathology = to_float(pathology_row.get("survival_steps_mean"))
    baseline = to_float(full_row.get("survival_steps_mean"))
    if pathology is None or baseline is None:
        return False
    return pathology < baseline


def to_float(value: object) -> float | None:
    if value in (None, "", "None"):
        return None
    return float(value)
