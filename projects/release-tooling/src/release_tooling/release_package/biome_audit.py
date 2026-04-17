"""Biome distribution audit."""

from __future__ import annotations

from collections import Counter, defaultdict


def build_biome_audit(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "total_counts": counts_payload(count_rows(rows)),
        "single_biome_only": len(count_rows(rows)) == 1,
        "single_biome_id": single_biome_id(rows),
        "by_input_root": input_root_payload(rows),
        "by_phase": phase_payload(rows),
        "by_mode_phase": mode_phase_payload(rows),
    }


def input_root_payload(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = group_counts(rows, ("input_name",))
    return payload_list(grouped, ("input_name",))


def phase_payload(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = group_counts(rows, ("phase",))
    return payload_list(grouped, ("phase",))


def mode_phase_payload(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = group_counts(rows, ("mode", "phase"))
    return payload_list(grouped, ("mode", "phase"))


def group_counts(
    rows: list[dict[str, object]],
    keys: tuple[str, ...],
) -> dict[tuple[object, ...], Counter[str]]:
    grouped: dict[tuple[object, ...], Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[tuple(row[key] for key in keys)][str(row.get("biome_id", "unknown"))] += 1
    return grouped


def payload_list(
    grouped: dict[tuple[object, ...], Counter[str]],
    keys: tuple[str, ...],
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for group_key, counts in sorted(grouped.items()):
        payload = dict(zip(keys, group_key, strict=True))
        payload["episode_count"] = sum(counts.values())
        payload["counts"] = counts_payload(counts)
        items.append(payload)
    return items


def count_rows(rows: list[dict[str, object]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(row.get("biome_id", "unknown"))] += 1
    return counts


def counts_payload(counts: Counter[str]) -> dict[str, int]:
    return {key: counts[key] for key in sorted(counts)}


def single_biome_id(rows: list[dict[str, object]]) -> str | None:
    counts = count_rows(rows)
    return next(iter(counts)) if len(counts) == 1 else None
