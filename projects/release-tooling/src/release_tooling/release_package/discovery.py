"""Run discovery from frozen artifact roots."""

from __future__ import annotations

import json
from pathlib import Path


PHASE_NAMES = {"core", "relocation"}


def discover_runs(input_roots: tuple[Path, ...]) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for input_root in input_roots:
        manifests = sorted(input_root.rglob("run_manifest.json"))
        runs.extend(build_run_record(input_root, path) for path in manifests)
    return runs


def build_run_record(input_root: Path, manifest_path: Path) -> dict[str, object]:
    payload = read_json(manifest_path)
    mode, phase = infer_mode_phase(manifest_path)
    return {
        "input_root": input_root,
        "input_name": input_root.name,
        "manifest_path": manifest_path,
        "log_path": manifest_path.parent / "logs" / "episode_summaries.jsonl",
        "run_id": payload["run_id"],
        "launch_seed": int(payload["base_seed"]),
        "config_hash": payload["config_hash"],
        "config_path_raw": payload.get("config_path"),
        "mode": mode,
        "phase": phase,
    }


def infer_mode_phase(manifest_path: Path) -> tuple[str, str]:
    parts = list(manifest_path.parts)
    seed_idx = next(index for index, part in enumerate(parts) if part.startswith("seed_"))
    phase = phase_after_seed(parts, seed_idx) or phase_before_seed(parts, seed_idx)
    mode = mode_before_seed(parts, seed_idx) or mode_before_phase(parts, seed_idx)
    if phase is None or mode is None:
        raise RuntimeError(f"Cannot infer mode/phase from {manifest_path}")
    return mode, phase


def phase_after_seed(parts: list[str], seed_idx: int) -> str | None:
    if seed_idx + 1 >= len(parts):
        return None
    candidate = parts[seed_idx + 1]
    return candidate if candidate in PHASE_NAMES else None


def phase_before_seed(parts: list[str], seed_idx: int) -> str | None:
    if seed_idx < 2:
        return None
    candidate = parts[seed_idx - 2]
    return candidate if candidate in PHASE_NAMES else None


def mode_before_seed(parts: list[str], seed_idx: int) -> str | None:
    if seed_idx < 1:
        return None
    candidate = parts[seed_idx - 1]
    return None if candidate in PHASE_NAMES else candidate


def mode_before_phase(parts: list[str], seed_idx: int) -> str | None:
    if seed_idx + 1 >= len(parts) or parts[seed_idx + 1] not in PHASE_NAMES:
        return None
    if seed_idx < 1:
        return None
    return parts[seed_idx - 1]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
