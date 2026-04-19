"""Artifacts for a continuous life-series run."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class LifeArtifactsWriter:
    root_dir: Path
    run_id: str

    @property
    def monitoring_dir(self) -> Path:
        return self.root_dir / "monitoring"

    @property
    def config_snapshot_path(self) -> Path:
        return self.root_dir / "run_config.yaml"

    @property
    def manifest_path(self) -> Path:
        return self.root_dir / "run_manifest.json"

    @property
    def life_summaries_path(self) -> Path:
        return self.root_dir / "life_summaries.jsonl"

    @property
    def window_metrics_path(self) -> Path:
        return self.root_dir / "window_metrics.jsonl"

    @property
    def event_metrics_path(self) -> Path:
        return self.root_dir / "event_metrics.jsonl"

    @property
    def series_metrics_path(self) -> Path:
        return self.root_dir / "series_metrics.jsonl"

    @property
    def slow_memory_path(self) -> Path:
        return self.root_dir / "slow_memory.npz"

    def setup(self, clean_existing: bool = False) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        if clean_existing:
            self._reset_known_paths()
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        for path in self._dataset_paths():
            path.touch(exist_ok=True)

    def write_yaml(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = yaml.safe_dump(payload, allow_unicode=True, default_flow_style=False, sort_keys=False)
        path.write_text(text, encoding="utf-8")
        return path

    def write_json(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def write_life_summary(self, row) -> None:
        self._append_rows(self.life_summaries_path, [row])

    def append_window_rows(self, rows: list) -> None:
        self._append_rows(self.window_metrics_path, rows)

    def append_event_rows(self, rows: list) -> None:
        self._append_rows(self.event_metrics_path, rows)

    def append_series_row(self, row) -> None:
        if row is not None:
            self._append_rows(self.series_metrics_path, [row])

    def _append_rows(self, path: Path, rows: list) -> None:
        if not rows:
            return
        lines = [json.dumps(asdict(row), ensure_ascii=False) for row in rows]
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

    def _reset_known_paths(self) -> None:
        for path in self._known_paths():
            if not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path)
                continue
            path.unlink()

    def _dataset_paths(self) -> tuple[Path, ...]:
        return (
            self.life_summaries_path,
            self.window_metrics_path,
            self.event_metrics_path,
            self.series_metrics_path,
        )

    def _known_paths(self) -> tuple[Path, ...]:
        return (
            self.monitoring_dir,
            self.config_snapshot_path,
            self.manifest_path,
            self.slow_memory_path,
            *self._dataset_paths(),
        )
