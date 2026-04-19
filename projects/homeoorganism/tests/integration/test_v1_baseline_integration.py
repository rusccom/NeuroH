from pathlib import Path

from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings


def test_v1_baseline_agent_runs_on_v2_env(tmp_path: Path):
    config_path = tmp_path / "v1-baseline.yaml"
    config_path.write_text(
        """run_id: v1-baseline
enable_monitoring: false
run_ablations: false
train_episodes: 1
eval_episodes_seen: 0
eval_episodes_relocation: 0
""",
        encoding="utf-8",
    )
    runtime = build_runtime(
        str(config_path),
        RuntimeSettings(tmp_path / "artifacts", run_id="v1-baseline", run_ablations=False, clean_artifacts=True),
        mode="v1_baseline_full",
    )
    try:
        report = runtime.orchestrator.run("v1_baseline_full", life_count=1, life_max_ticks=200)
    finally:
        runtime.monitoring.recorder.close()
    assert report.completed_lives == 1
    assert report.life_states[0].tick <= 200
    assert runtime.artifacts.life_summaries_path.read_text(encoding="utf-8").strip()
