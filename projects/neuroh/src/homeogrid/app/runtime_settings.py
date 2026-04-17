"""Runtime build settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeSettings:
    artifacts_root: Path = Path("artifacts")
    run_id: str | None = None
    base_seed: int | None = None
    run_ablations: bool | None = None
    clean_artifacts: bool = False
