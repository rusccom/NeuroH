"""Artifact layout for a single run."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class RunArtifacts:
    root_dir: Path
    run_id: str

    @property
    def reports_dir(self) -> Path:
        return self.root_dir / "reports"

    @property
    def logs_dir(self) -> Path:
        return self.root_dir / "logs"

    @property
    def memory_dir(self) -> Path:
        return self.root_dir / "memory"

    @property
    def monitoring_dir(self) -> Path:
        return self.root_dir / "monitoring"

    @property
    def snapshots_dir(self) -> Path:
        return self.root_dir / "snapshots"

    @property
    def metrics_path(self) -> Path:
        return self.reports_dir / "metrics.csv"

    @property
    def ablations_path(self) -> Path:
        return self.reports_dir / "ablation_results.csv"

    @property
    def summaries_path(self) -> Path:
        return self.logs_dir / "episode_summaries.jsonl"

    @property
    def slow_memory_path(self) -> Path:
        return self.memory_dir / "slow_memory.npz"

    @property
    def config_snapshot_path(self) -> Path:
        return self.root_dir / "run_config.yaml"

    @property
    def manifest_path(self) -> Path:
        return self.root_dir / "run_manifest.json"

    def setup(self, clean_existing: bool = False) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        if clean_existing:
            self._reset_known_paths()
        for directory in self._directories():
            directory.mkdir(parents=True, exist_ok=True)

    def write_yaml(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = yaml.safe_dump(
            payload,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        path.write_text(text, encoding="utf-8")
        return path

    def write_json(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _directories(self) -> tuple[Path, ...]:
        return (
            self.reports_dir,
            self.logs_dir,
            self.memory_dir,
            self.monitoring_dir,
            self.snapshots_dir,
        )

    def _reset_known_paths(self) -> None:
        for path in self._known_paths():
            self._reset_path(path)

    def _known_paths(self) -> tuple[Path, ...]:
        return (
            self.reports_dir,
            self.logs_dir,
            self.memory_dir,
            self.monitoring_dir,
            self.snapshots_dir,
            self.config_snapshot_path,
            self.manifest_path,
        )

    def _reset_path(self, path: Path) -> None:
        if not path.exists():
            return
        if path.is_dir():
            shutil.rmtree(path)
            return
        path.unlink()
