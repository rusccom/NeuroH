"""Load and enrich per-episode truth rows."""

from __future__ import annotations

import json

from release_tooling.release_package.config_paths import read_relocation_step


def load_episode_rows(runs: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for run in runs:
        rows.extend(load_run_rows(run))
    return rows


def load_run_rows(run: dict[str, object]) -> list[dict[str, object]]:
    relocation_step = read_relocation_step(run) if run["phase"] == "relocation" else None
    items: list[dict[str, object]] = []
    for row in read_jsonl(run["log_path"]):
        items.append(enrich_row(run, row, relocation_step))
    return items


def enrich_row(
    run: dict[str, object],
    row: dict[str, object],
    relocation_step: int | None,
) -> dict[str, object]:
    enriched = dict(row)
    enriched["input_name"] = run["input_name"]
    enriched["phase"] = run["phase"]
    enriched["mode"] = run["mode"]
    enriched["seed"] = run["launch_seed"]
    enriched["run_id"] = run["run_id"]
    enriched["config_hash"] = run["config_hash"]
    enriched["post_relocation_life"] = build_post_relocation_life(row, relocation_step)
    return enriched


def build_post_relocation_life(row: dict[str, object], relocation_step: int | None) -> int | None:
    if relocation_step is None:
        return None
    survival_steps = to_float(row.get("survival_steps"))
    if survival_steps is None:
        return None
    return int(survival_steps - relocation_step)


def read_jsonl(path: object) -> list[dict[str, object]]:
    file_path = path
    lines = file_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def to_float(value: object) -> float | None:
    if value is None or value in ("", "None", "True", "False"):
        return None
    if isinstance(value, bool):
        return None
    return float(value)
