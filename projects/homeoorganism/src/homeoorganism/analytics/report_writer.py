"""Artifact report writing."""

from __future__ import annotations

import csv
import json
from pathlib import Path


class ReportWriter:
    def __init__(self, artifacts_root: str = "artifacts") -> None:
        self._root = Path(artifacts_root)
        self._reports = self._root / "reports"
        self._logs = self._root / "logs"
        self._reports.mkdir(parents=True, exist_ok=True)
        self._logs.mkdir(parents=True, exist_ok=True)

    def write_metrics(self, rows: list[dict]) -> None:
        self._write_csv(self._reports / "metrics.csv", rows)

    def write_ablations(self, rows: list[dict]) -> None:
        self._write_csv(self._reports / "ablation_results.csv", rows)

    def append_summary(self, row: dict) -> None:
        file_path = self._logs / "episode_summaries.jsonl"
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _write_csv(self, path: Path, rows: list[dict]) -> None:
        if not rows:
            return
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
