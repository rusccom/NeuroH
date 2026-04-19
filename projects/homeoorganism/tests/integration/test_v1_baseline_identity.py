"""RC4 regression guard for active-vs-baseline agent identity."""

from pathlib import Path

from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings


def test_continuous_full_and_v1_baseline_full_produce_identical_lives(tmp_path: Path):
    config_path = tmp_path / "identity.yaml"
    config_path.write_text(
        """run_id: identity-check
enable_monitoring: false
run_ablations: false
train_episodes: 1
eval_episodes_seen: 0
eval_episodes_relocation: 0
""",
        encoding="utf-8",
    )
    active_report = _run_mode(tmp_path, config_path, "continuous_full", "active")
    baseline_report = _run_mode(tmp_path, config_path, "v1_baseline_full", "baseline")
    active_life = active_report.life_states[0]
    baseline_life = baseline_report.life_states[0]
    assert active_life.tick == baseline_life.tick
    assert active_life.end_reason == baseline_life.end_reason


def _run_mode(tmp_path: Path, config_path: Path, mode: str, run_id: str):
    settings = RuntimeSettings(
        artifacts_root=tmp_path / run_id,
        run_id=run_id,
        run_ablations=False,
        clean_artifacts=True,
    )
    runtime = build_runtime(str(config_path), settings, mode=mode)
    try:
        return runtime.orchestrator.run(mode, life_count=1, life_max_ticks=300)
    finally:
        runtime.monitoring.recorder.close()
