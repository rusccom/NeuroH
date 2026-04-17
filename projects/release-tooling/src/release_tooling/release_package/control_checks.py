"""Control check evaluation."""

from __future__ import annotations


NEAR_ZERO = 1e-9


def build_control_checks(summary_rows: list[dict[str, object]]) -> dict[str, bool]:
    grouped = group_modes(summary_rows)
    return {
        "full_slow_gt_zero": all_metric(grouped.get("full", []), "source_slow_share", lambda value: value > 0.0),
        "no_slow_slow_near_zero": all_metric(grouped.get("no_slow", []), "source_slow_share", lambda value: value <= NEAR_ZERO),
        "no_fast_fast_near_zero": all_metric(grouped.get("no_fast", []), "source_fast_share", lambda value: value <= NEAR_ZERO),
    }


def group_modes(summary_rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in summary_rows:
        grouped.setdefault(str(row["mode"]), []).append(row)
    return grouped


def all_metric(
    rows: list[dict[str, object]],
    metric: str,
    predicate: object,
) -> bool:
    if not rows:
        return False
    return all(predicate(float(row[metric])) for row in rows if row.get(metric) is not None)
