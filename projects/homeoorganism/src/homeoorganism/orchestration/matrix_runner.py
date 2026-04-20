"""Experiment matrix orchestration."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from homeoorganism.analytics.matrix_summary_builder import MatrixSummaryBuilder
from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings
from homeoorganism.config.loader import load_config
from homeoorganism.orchestration.seed_set import SeedSet

LIFE_MODES = frozenset({"continuous_full", "continuous_no_regen", "v1_baseline_full"})


@dataclass(frozen=True)
class ExperimentMatrixRunner:
    config_path: Path
    seeds_path: Path
    modes: tuple[str, ...]
    summary_name: str = "matrix_summary.csv"

    def run(self) -> dict[str, object]:
        seeds = SeedSet(self.seeds_path).load()
        modes = self._resolve_modes()
        rows = []
        for mode in modes:
            for seed in seeds:
                rows.extend(self._run_one(mode, seed))
        summary_path = self._write_summary(rows)
        return self._result(summary_path, seeds, modes)

    def _resolve_modes(self) -> tuple[str, ...]:
        if self.modes:
            return self.modes
        config = load_config(self.config_path)
        return config.experiment.ablation_modes

    def _run_one(self, mode: str, seed: int) -> list[dict[str, str]]:
        runtime = build_runtime(str(self.config_path), self._settings(mode, seed), mode)
        try:
            self._run_mode(runtime, mode)
            return self._load_run_rows(runtime, mode, seed)
        finally:
            runtime.monitoring.recorder.close()

    def _settings(self, mode: str, seed: int) -> RuntimeSettings:
        return RuntimeSettings(
            artifacts_root=Path("artifacts") / "runs" / mode / f"seed_{seed}",
            run_id=f"{mode}-seed-{seed}",
            base_seed=seed,
            run_ablations=False,
            clean_artifacts=True,
        )

    def _run_mode(self, runtime, mode: str) -> None:
        if mode in LIFE_MODES:
            runtime.orchestrator.run(
                mode,
                runtime.config.experiment.lives_per_seed,
                runtime.config.experiment.life_max_ticks,
            )
            return
        runtime.orchestrator.run_protocol(
            "full",
            train_episodes=0,
            eval_seen_episodes=runtime.config.experiment.lives_per_seed,
            eval_relocation_episodes=0,
        )

    def _load_run_rows(self, runtime, mode: str, seed: int) -> list[dict[str, str]]:
        if mode in LIFE_MODES:
            return self._load_life_rows(runtime.artifacts.life_summaries_path, mode, seed)
        return self._load_csv_rows(runtime.artifacts.metrics_path)

    def _load_csv_rows(self, metrics_path: Path) -> list[dict[str, str]]:
        with metrics_path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _load_life_rows(self, summaries_path: Path, mode: str, seed: int) -> list[dict[str, str]]:
        rows = []
        for line in summaries_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row.update({"mode": mode, "phase": "life", "seed": seed})
            rows.append(row)
        return rows

    def _write_summary(self, rows: list[dict[str, str]]) -> Path:
        summary_rows = MatrixSummaryBuilder().build(rows)
        output_path = Path("artifacts") / "aggregate" / self.summary_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_csv(output_path, summary_rows)
        return output_path

    def _write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def _result(self, summary_path: Path, seeds: tuple[int, ...], modes: tuple[str, ...]) -> dict[str, object]:
        return {
            "summary_path": str(summary_path),
            "seed_count": len(seeds),
            "run_count": len(seeds) * len(modes),
            "modes": list(modes),
            "seeds": list(seeds),
        }
