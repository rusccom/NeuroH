"""CLI entrypoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from homeogrid.app.replay import replay_file
from homeogrid.app.run import run_runtime
from homeogrid.orchestration.freeze_manager import FreezeManager
from homeogrid.orchestration.matrix_runner import ExperimentMatrixRunner
from homeogrid.orchestration.reproducibility_checker import ReproducibilityChecker
from homeogrid.orchestration.soak_runner import SoakRunner


def main() -> None:
    parser = argparse.ArgumentParser(prog="homeogrid")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", required=True)
    ablate_parser = subparsers.add_parser("ablate")
    ablate_parser.add_argument("--config", required=True)
    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--file", required=True)
    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--tag", default="mvp-rc3")
    freeze_parser.add_argument("--config", action="append")
    freeze_parser.add_argument("--seeds", action="append")
    matrix_parser = subparsers.add_parser("run-matrix")
    matrix_parser.add_argument("--config", required=True)
    matrix_parser.add_argument("--seeds", required=True)
    matrix_parser.add_argument("--modes")
    matrix_parser.add_argument("--summary-name", default="matrix_summary.csv")
    repro_parser = subparsers.add_parser("repro-check")
    repro_parser.add_argument("--config", required=True)
    repro_parser.add_argument("--seed", required=True, type=int)
    repro_parser.add_argument("--mode", default="full")
    repro_parser.add_argument("--episodes", default=1, type=int)
    soak_parser = subparsers.add_parser("soak")
    soak_parser.add_argument("--config", required=True)
    soak_parser.add_argument("--seed", default=42, type=int)
    soak_parser.add_argument("--mode", default="full")
    soak_parser.add_argument("--episodes", required=True, type=int)
    args = parser.parse_args()
    if args.command == "replay":
        print(json.dumps(replay_file(args.file), ensure_ascii=False, indent=2))
        return
    if args.command == "freeze":
        manager = FreezeManager(args.tag, _freeze_configs(args.config), _freeze_seeds(args.seeds))
        print(json.dumps(manager.freeze(), ensure_ascii=False, indent=2))
        return
    if args.command == "run-matrix":
        runner = ExperimentMatrixRunner(
            config_path=Path(args.config),
            seeds_path=Path(args.seeds),
            modes=_parse_modes(args.modes),
            summary_name=args.summary_name,
        )
        print(json.dumps(runner.run(), ensure_ascii=False, indent=2))
        return
    if args.command == "repro-check":
        checker = ReproducibilityChecker(Path(args.config), args.mode, args.seed, args.episodes)
        print(json.dumps(checker.run(), ensure_ascii=False, indent=2))
        return
    if args.command == "soak":
        runner = SoakRunner(Path(args.config), args.mode, args.seed, args.episodes)
        print(json.dumps(runner.run(), ensure_ascii=False, indent=2))
        return
    run_runtime(args.config, args.command)


def _parse_modes(raw_modes: str | None) -> tuple[str, ...]:
    if raw_modes is None:
        return ()
    return tuple(mode.strip() for mode in raw_modes.split(",") if mode.strip())


def _paths(raw_paths: list[str]) -> tuple[Path, ...]:
    return tuple(Path(path) for path in raw_paths)


def _freeze_configs(raw_paths: list[str] | None) -> tuple[Path, ...]:
    default_paths = [
        "configs/full.yaml",
        "configs/ablation.yaml",
        "configs/rc3_calibration.yaml",
    ]
    return _paths(default_paths if raw_paths is None else raw_paths)


def _freeze_seeds(raw_paths: list[str] | None) -> tuple[Path, ...]:
    default_paths = ["configs/seeds/official.txt", "configs/seeds/pilot.txt"]
    return _paths(default_paths if raw_paths is None else raw_paths)


if __name__ == "__main__":
    main()
