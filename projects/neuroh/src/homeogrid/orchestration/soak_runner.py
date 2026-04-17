"""Long-running soak execution."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean

from homeogrid.app.run import build_runtime
from homeogrid.app.runtime_settings import RuntimeSettings


@dataclass(frozen=True)
class SoakRunner:
    config_path: Path
    mode: str
    seed: int
    episodes: int

    def run(self) -> dict[str, object]:
        runtime = build_runtime(str(self.config_path), self._settings())
        try:
            runtime.orchestrator.run_protocol(
                self.mode,
                train_episodes=self.episodes,
                eval_seen_episodes=0,
                eval_relocation_episodes=0,
            )
        finally:
            runtime.monitoring.recorder.close()
        summary = self._summary(runtime.artifacts.root_dir, runtime.config.experiment.run_id)
        self._summary_path().write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        summary["summary_path"] = str(self._summary_path())
        return summary

    def _settings(self) -> RuntimeSettings:
        return RuntimeSettings(
            artifacts_root=Path("artifacts") / "soak" / self.mode / f"seed_{self.seed}",
            run_id=f"soak-{self.mode}-seed-{self.seed}",
            base_seed=self.seed,
            run_ablations=False,
            clean_artifacts=True,
        )

    def _summary(self, root_dir: Path, run_id: str) -> dict[str, object]:
        rows = self._load_rows(root_dir / "reports" / "metrics.csv")
        return {
            "mode": self.mode,
            "seed": self.seed,
            "episodes_requested": self.episodes,
            "episodes_completed": len(rows),
            "mean_survival_steps": self._mean_metric(rows, "survival_steps"),
            "mean_energy_deficit": self._mean_metric(rows, "mean_energy_deficit"),
            "mean_water_deficit": self._mean_metric(rows, "mean_water_deficit"),
            "replay_files": len(list((root_dir / "monitoring" / run_id).glob("*.jsonl"))),
            "root_dir": str(root_dir),
        }

    def _load_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _mean_metric(self, rows: list[dict[str, str]], name: str) -> float:
        values = [float(row[name]) for row in rows if row.get(name)]
        return 0.0 if not values else fmean(values)

    def _summary_path(self) -> Path:
        path = Path("artifacts") / "soak" / self.mode / f"seed_{self.seed}" / "soak_summary.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
