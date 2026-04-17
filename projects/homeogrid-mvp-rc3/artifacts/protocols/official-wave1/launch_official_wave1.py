from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from official_wave1_manifest import write_manifest

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_DIR = ROOT / "artifacts" / "protocols" / "official-wave1"
OUTPUT_DIR = ROOT / "artifacts" / "official_wave1"
AGGREGATE_DIR = ROOT / "artifacts" / "aggregate"
LOG_PATH = PROTOCOL_DIR / "command_log.txt"
MANIFEST_PATH = PROTOCOL_DIR / "official_wave1_manifest.json"
CORE_CONFIG_PATH = PROTOCOL_DIR / "official_core.yaml"
RELOCATION_CONFIG_PATH = PROTOCOL_DIR / "official_relocation.yaml"
BASELINE_COMMIT = "7ffb5e04a022f7b905b002719dca35ef330e5b90"
BASELINE_TAG = "mvp-rc3"
MODES = ("full", "no_fast", "no_slow", "no_interoception")


def main() -> None:
    _bootstrap_src()
    _assert_clean_worktree()
    PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)
    _reset_log()
    seeds = _official_seeds()
    core_config = _write_core_config()
    relocation_config = _write_relocation_config()
    write_manifest(
        root=ROOT,
        manifest_path=MANIFEST_PATH,
        output_dir=OUTPUT_DIR,
        core_config=core_config,
        relocation_config=relocation_config,
        baseline_tag=BASELINE_TAG,
        baseline_commit=BASELINE_COMMIT,
        modes=MODES,
    )
    _log(f"baseline={BASELINE_TAG} commit={BASELINE_COMMIT}")
    _run_core_phase(core_config, seeds)
    _run_relocation_phase(relocation_config, seeds)
    packet_paths = _build_packet()
    _log(f"packet_review={packet_paths['review']}")
    print(json.dumps(_result(core_config, relocation_config, packet_paths), ensure_ascii=False, indent=2))


def _bootstrap_src() -> None:
    src_path = str(ROOT / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def _assert_clean_worktree() -> None:
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--short")
    if head != BASELINE_COMMIT:
        raise RuntimeError(f"Expected {BASELINE_COMMIT}, got {head}")
    if status:
        raise RuntimeError(f"Worktree must be clean before launch:\n{status}")


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _official_seeds() -> tuple[int, ...]:
    from homeogrid.orchestration.seed_set import SeedSet

    return SeedSet(ROOT / "configs" / "seeds" / "official.txt").load()


def _write_core_config() -> Path:
    data = _load_yaml(ROOT / "configs" / "ablation.yaml")
    data.update(_core_experiment())
    _write_yaml(CORE_CONFIG_PATH, data)
    return CORE_CONFIG_PATH


def _core_experiment() -> dict[str, object]:
    return {
        "run_id": "official-wave1-core",
        "train_episodes": 200,
        "eval_episodes_seen": 100,
        "eval_episodes_relocation": 0,
        "run_ablations": False,
        "ablation_modes": list(MODES),
    }


def _write_relocation_config() -> Path:
    data = _load_yaml(ROOT / "configs" / "rc3_calibration.yaml")
    data.update(_relocation_experiment())
    _write_yaml(RELOCATION_CONFIG_PATH, data)
    return RELOCATION_CONFIG_PATH


def _relocation_experiment() -> dict[str, object]:
    return {
        "run_id": "official-wave1-relocation",
        "train_episodes": 0,
        "eval_episodes_seen": 0,
        "eval_episodes_relocation": 50,
        "run_ablations": False,
        "ablation_modes": list(MODES),
    }

def _run_core_phase(config_path: Path, seeds: tuple[int, ...]) -> None:
    for mode in MODES:
        for seed in seeds:
            root = _phase_root("core", mode, seed)
            run_id = f"official-core-{mode}-seed-{seed}"
            _log(f"core start mode={mode} seed={seed} root={_rel(root)}")
            _execute_run(config_path, root, run_id, mode, seed, clean=True)
            _verify_core_outputs(root)
            _log(f"core done mode={mode} seed={seed}")


def _run_relocation_phase(config_path: Path, seeds: tuple[int, ...]) -> None:
    for mode in MODES:
        for seed in seeds:
            core_root = _phase_root("core", mode, seed)
            relocation_root = _phase_root("relocation", mode, seed)
            _prepare_relocation_root(core_root, relocation_root)
            run_id = f"official-relocation-{mode}-seed-{seed}"
            _log(f"relocation start mode={mode} seed={seed} root={_rel(relocation_root)}")
            _execute_run(config_path, relocation_root, run_id, mode, seed, clean=False)
            _verify_relocation_outputs(relocation_root)
            _log(f"relocation done mode={mode} seed={seed}")


def _execute_run(
    config_path: Path,
    artifacts_root: Path,
    run_id: str,
    mode: str,
    seed: int,
    clean: bool,
) -> None:
    from homeogrid.app.run import build_runtime
    from homeogrid.app.runtime_settings import RuntimeSettings

    settings = RuntimeSettings(
        artifacts_root=artifacts_root,
        run_id=run_id,
        base_seed=seed,
        run_ablations=False,
        clean_artifacts=clean,
    )
    runtime = build_runtime(str(config_path), settings)
    try:
        runtime.orchestrator.run_protocol(mode)
    finally:
        runtime.monitoring.recorder.close()


def _prepare_relocation_root(core_root: Path, relocation_root: Path) -> None:
    _verify_core_outputs(core_root)
    if relocation_root.exists():
        shutil.rmtree(relocation_root)
    target_memory = relocation_root / "memory"
    target_memory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(core_root / "memory" / "slow_memory.npz", target_memory / "slow_memory.npz")


def _verify_core_outputs(root: Path) -> None:
    required = (
        root / "reports" / "metrics.csv",
        root / "memory" / "slow_memory.npz",
        root / "logs" / "episode_summaries.jsonl",
    )
    for path in required:
        _require_file(path)


def _verify_relocation_outputs(root: Path) -> None:
    metrics_path = root / "reports" / "metrics.csv"
    summaries_path = root / "logs" / "episode_summaries.jsonl"
    _require_file(metrics_path)
    _require_file(summaries_path)
    _require_metric_columns(metrics_path, ("relocation_recovery_success_rate", "relocation_recovery_steps"))
    if not list(root.glob("monitoring/*/*.jsonl")):
        raise RuntimeError(f"Missing monitoring JSONL in {root}")


def _require_metric_columns(metrics_path: Path, columns: tuple[str, ...]) -> None:
    with metrics_path.open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle), [])
    missing = [column for column in columns if column not in header]
    if missing:
        raise RuntimeError(f"Missing columns {missing} in {metrics_path}")


def _build_packet() -> dict[str, str]:
    from build_official_packet import build_packet

    return build_packet(PROTOCOL_DIR, OUTPUT_DIR, AGGREGATE_DIR)


def _phase_root(phase: str, mode: str, seed: int) -> Path:
    return OUTPUT_DIR / phase / mode / f"seed_{seed}"


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    text = yaml.safe_dump(payload, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(text, encoding="utf-8")


def _reset_log() -> None:
    LOG_PATH.write_text("", encoding="utf-8")


def _log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{_timestamp()} {message}\n")


def _require_file(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing expected artifact: {path}")

def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _result(
    core_config: Path,
    relocation_config: Path,
    packet_paths: dict[str, str],
) -> dict[str, object]:
    return {
        "manifest": str(MANIFEST_PATH),
        "command_log": str(LOG_PATH),
        "core_config": str(core_config),
        "relocation_config": str(relocation_config),
        "output_root": str(OUTPUT_DIR),
        "packet_paths": packet_paths,
    }


if __name__ == "__main__":
    main()
