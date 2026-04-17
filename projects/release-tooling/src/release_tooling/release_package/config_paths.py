"""Helpers for locating launch configs and relocation settings."""

from __future__ import annotations

from pathlib import Path


def resolve_config_path(run: dict[str, object]) -> Path | None:
    raw_path = run.get("config_path_raw")
    if not raw_path:
        return None
    direct = Path(str(raw_path))
    if direct.exists():
        return direct
    filename = direct.name
    return search_protocol_dirs(Path(run["manifest_path"]), filename)


def search_protocol_dirs(manifest_path: Path, filename: str) -> Path | None:
    for ancestor in manifest_path.parents:
        candidate_root = ancestor / "artifacts" / "protocols"
        if not candidate_root.exists():
            continue
        match = next(candidate_root.rglob(filename), None)
        if match is not None:
            return match
    return None


def read_relocation_step(run: dict[str, object]) -> int | None:
    config_path = resolve_config_path(run)
    if config_path is None:
        return None
    return parse_env_scalar(config_path, "relocation_step")


def parse_env_scalar(path: Path, key: str) -> int | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    env_block = slice_env_block(lines)
    if env_block is None:
        return None
    return parse_scalar(env_block, key)


def slice_env_block(lines: list[str]) -> list[str] | None:
    start = find_env_start(lines)
    if start is None:
        return None
    block: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line.startswith("  "):
            break
        block.append(line)
    return block


def find_env_start(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.strip() == "env:":
            return index
    return None


def parse_scalar(lines: list[str], key: str) -> int | None:
    prefix = f"  {key}:"
    for line in lines:
        if not line.startswith(prefix):
            continue
        raw = line.split(":", maxsplit=1)[1].strip()
        return int(float(raw))
    return None
