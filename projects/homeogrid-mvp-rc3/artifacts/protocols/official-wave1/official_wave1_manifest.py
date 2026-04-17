from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path


def write_manifest(
    root: Path,
    manifest_path: Path,
    output_dir: Path,
    core_config: Path,
    relocation_config: Path,
    baseline_tag: str,
    baseline_commit: str,
    modes: tuple[str, ...],
) -> None:
    payload = {
        "baseline_tag": baseline_tag,
        "baseline_commit": baseline_commit,
        "created_at_utc": _timestamp(),
        "source_configs": _source_entries(root),
        "launch_configs": _launch_entries(root, core_config, relocation_config),
        "modes": list(modes),
        "seed_source": _file_entry(root, root / "configs" / "seeds" / "official.txt"),
        "split_flow": _split_flow(),
        "artifacts_root": _rel(root, output_dir),
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _source_entries(root: Path) -> list[dict[str, object]]:
    paths = (
        root / "configs" / "ablation.yaml",
        root / "configs" / "rc3_calibration.yaml",
    )
    return [_file_entry(root, path) for path in paths]


def _launch_entries(root: Path, core_config: Path, relocation_config: Path) -> dict[str, dict[str, object]]:
    return {
        "core": _launch_entry(root, core_config, 200, 100, 0),
        "relocation": _launch_entry(root, relocation_config, 0, 0, 50),
    }


def _launch_entry(path_root: Path, path: Path, train: int, eval_seen: int, eval_relocation: int) -> dict[str, object]:
    entry = _file_entry(path_root, path)
    entry["train"] = train
    entry["eval_seen"] = eval_seen
    entry["eval_relocation"] = eval_relocation
    if path.name == "official_relocation.yaml":
        entry["relocation_step"] = 45
        entry["relocation_probability"] = 1.0
    return entry


def _split_flow() -> dict[str, object]:
    return {
        "phase_a": "core",
        "phase_b": "relocation",
        "reuse_rule": "copy slow_memory from corresponding core run into relocation root before runtime build",
    }


def _file_entry(root: Path, path: Path) -> dict[str, object]:
    return {"path": _rel(root, path), "sha256": sha256(path.read_bytes()).hexdigest()}


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
