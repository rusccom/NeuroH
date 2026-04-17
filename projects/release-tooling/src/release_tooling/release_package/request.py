"""Request payload for release assembly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReleaseRequest:
    package_name: str
    baseline_tag: str
    baseline_commit: str
    input_roots: tuple[Path, ...]
    output_root: Path
