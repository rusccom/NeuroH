"""Reproducibility checks for a fixed scenario."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings


@dataclass(frozen=True)
class ReproducibilityChecker:
    config_path: Path
    mode: str
    seed: int
    episodes: int = 1

    def run(self) -> dict[str, object]:
        left = self._execute_repeat(1)
        right = self._execute_repeat(2)
        report = self._build_report(left, right)
        self._report_path().write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report_path"] = str(self._report_path())
        return report

    def _execute_repeat(self, repeat: int) -> dict[str, object]:
        runtime = build_runtime(str(self.config_path), self._settings(repeat))
        try:
            runtime.orchestrator.run_protocol(
                self.mode,
                train_episodes=self.episodes,
                eval_seen_episodes=0,
                eval_relocation_episodes=0,
            )
        finally:
            runtime.monitoring.recorder.close()
        return {
            "root_dir": str(runtime.artifacts.root_dir),
            "metrics": self._load_metrics(runtime.artifacts.metrics_path),
            "sequences": self._load_sequences(runtime.artifacts.monitoring_dir / runtime.config.experiment.run_id),
            "event_counts": self._load_event_counts(runtime.artifacts.monitoring_dir / runtime.config.experiment.run_id),
            "slow_memory": self._load_memory(runtime.artifacts.slow_memory_path),
        }

    def _settings(self, repeat: int) -> RuntimeSettings:
        return RuntimeSettings(
            artifacts_root=self._report_root() / f"repeat_{repeat}",
            run_id=f"repro-{self.mode}-seed-{self.seed}",
            base_seed=self.seed,
            run_ablations=False,
            clean_artifacts=True,
        )

    def _load_metrics(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _load_sequences(self, replay_dir: Path) -> dict[str, list[str]]:
        sequences = {}
        for path in sorted(replay_dir.glob("*.jsonl")):
            sequences[path.stem] = self._decision_sequence(path)
        return sequences

    def _decision_sequence(self, path: Path) -> list[str]:
        sequence = []
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record["type"] != "frame":
                continue
            sequence.append(record["payload"]["memory"]["decision_source"])
        return sequence

    def _load_event_counts(self, replay_dir: Path) -> dict[str, int]:
        counts = {}
        for path in sorted(replay_dir.glob("*.jsonl")):
            counts[path.stem] = self._event_count(path)
        return counts

    def _event_count(self, path: Path) -> int:
        count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record["type"] != "alert":
                continue
            count += 1
        return count

    def _load_memory(self, path: Path) -> dict[str, object]:
        data = np.load(path, allow_pickle=False)
        return {
            "episode_count": int(data["episode_count"]),
            "config_hash": str(data["config_hash"]),
            "heatmaps": data["heatmaps"].tolist(),
        }

    def _build_report(self, left: dict[str, object], right: dict[str, object]) -> dict[str, object]:
        return {
            "mode": self.mode,
            "seed": self.seed,
            "episodes": self.episodes,
            "metrics_match": left["metrics"] == right["metrics"],
            "decision_sequence_match": left["sequences"] == right["sequences"],
            "event_counts_match": left["event_counts"] == right["event_counts"],
            "slow_memory_match": left["slow_memory"] == right["slow_memory"],
            "matches": self._all_match(left, right),
            "left_root": left["root_dir"],
            "right_root": right["root_dir"],
        }

    def _all_match(self, left: dict[str, object], right: dict[str, object]) -> bool:
        return (
            left["metrics"] == right["metrics"]
            and left["sequences"] == right["sequences"]
            and left["event_counts"] == right["event_counts"]
            and left["slow_memory"] == right["slow_memory"]
        )

    def _report_root(self) -> Path:
        return Path("artifacts") / "reproducibility" / self.mode / f"seed_{self.seed}"

    def _report_path(self) -> Path:
        path = self._report_root() / "report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
