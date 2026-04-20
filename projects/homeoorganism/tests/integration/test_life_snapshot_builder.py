from pathlib import Path

from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings
from homeoorganism.monitoring.domain.life_snapshot import LifeSnapshot


def test_life_snapshot_reports_current_life_state(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, "state", enable_monitoring=False)
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=20)
    finally:
        runtime.monitoring.recorder.close()
    snapshot = runtime.monitoring.latest_snapshot()
    assert isinstance(snapshot, LifeSnapshot)
    assert snapshot.life_id == 1
    assert snapshot.current_tick <= 20
    assert snapshot.life_max_ticks == 20
    assert snapshot.completed_lives[0].life_id == 1


def test_life_snapshot_reports_rolling_metrics_after_first_window(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, "rolling", enable_monitoring=False, base_energy_cost=0, base_water_cost=0)
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=120)
    finally:
        runtime.monitoring.recorder.close()
    snapshot = runtime.monitoring.latest_snapshot()
    assert snapshot.current_energy_ratio_100 is not None
    assert snapshot.current_water_ratio_100 is not None
    assert snapshot.current_deficit_variance is not None


def test_life_snapshot_before_first_window_has_none_metrics(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, "pre-window", enable_monitoring=False, base_energy_cost=0, base_water_cost=0)
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=50)
    finally:
        runtime.monitoring.recorder.close()
    snapshot = runtime.monitoring.latest_snapshot()
    assert snapshot.current_energy_ratio_100 is None
    assert snapshot.current_water_ratio_100 is None
    assert snapshot.current_deficit_variance is None


def test_life_snapshot_reports_ecology_state(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, "ecology", enable_monitoring=False)
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=2)
    finally:
        runtime.monitoring.recorder.close()
    snapshot = runtime.monitoring.latest_snapshot()
    assert snapshot.current_food_count >= 0
    assert snapshot.current_water_count >= 0
    assert snapshot.next_relocation_tick == 1000


def test_life_snapshot_accumulates_completed_lives(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, "completed", energy_start=1, enable_monitoring=False)
    captured = []
    original_publish = runtime.monitoring.publish_step

    def publish(snapshot):
        captured.append(snapshot)
        return original_publish(snapshot)

    runtime.monitoring.publish_step = publish
    try:
        runtime.orchestrator.run("continuous_full", life_count=3, life_max_ticks=3)
    finally:
        runtime.monitoring.recorder.close()
    third_life = [snapshot for snapshot in captured if snapshot.life_id == 3]
    assert third_life
    assert len(third_life[0].completed_lives) == 2


def _build_life_runtime(
    tmp_path: Path,
    run_id: str,
    energy_start: int = 70,
    enable_monitoring: bool = False,
    base_energy_cost: int = 1,
    base_water_cost: int = 1,
):
    config_path = tmp_path / f"{run_id}.yaml"
    config_path.write_text(
        _config_text(run_id, energy_start, enable_monitoring, base_energy_cost, base_water_cost),
        encoding="utf-8",
    )
    settings = RuntimeSettings(
        artifacts_root=tmp_path / "artifacts",
        run_id=run_id,
        run_ablations=False,
        clean_artifacts=True,
    )
    return build_runtime(str(config_path), settings, mode="continuous_full")


def _config_text(
    run_id: str,
    energy_start: int,
    enable_monitoring: bool,
    base_energy_cost: int,
    base_water_cost: int,
) -> str:
    return f"""run_id: {run_id}
mode: continuous_full
enable_monitoring: {str(enable_monitoring).lower()}
run_ablations: false
train_episodes: 0
eval_episodes_seen: 0
eval_episodes_relocation: 0
lives_per_seed: 3
life_max_ticks: 120
body:
  energy_start: {energy_start}
  water_start: 70
  base_energy_cost: {base_energy_cost}
  base_water_cost: {base_water_cost}
"""
