"""Result payload for release assembly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssemblyResult:
    release_table_path: Path
    release_comparisons_path: Path
    biome_audit_path: Path
    official_verdict_path: Path
    report_path: Path
    run_count: int
    episode_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "release_table": str(self.release_table_path),
            "release_comparisons": str(self.release_comparisons_path),
            "biome_audit": str(self.biome_audit_path),
            "official_verdict": str(self.official_verdict_path),
            "report": str(self.report_path),
            "run_count": self.run_count,
            "episode_count": self.episode_count,
        }
