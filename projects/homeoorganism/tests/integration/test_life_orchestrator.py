import json
from pathlib import Path

from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings
from homeoorganism.orchestration.life_orchestrator import LifeOrchestrator
from homeoorganism.orchestration.life_state_store import LifeRuntime


def test_life_runtime_finalizes_to_life_state():
    runtime = LifeRuntime(life_id=3, tick=12, started_at_ts_ms=1000)
    state = runtime.finalize("max_ticks_reached")
    assert state.life_id == 3
    assert state.tick == 12
    assert state.started_at_ts_ms == 1000
    assert state.ended_at_ts_ms is not None
    assert state.end_reason == "max_ticks_reached"


def test_build_runtime_selects_life_orchestrator(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="dispatch")
    try:
        assert isinstance(runtime.orchestrator, LifeOrchestrator)
    finally:
        runtime.monitoring.recorder.close()


def test_life_ends_on_depletion(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="depletion", energy_start=1)
    try:
        report = runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=50)
    finally:
        runtime.monitoring.recorder.close()
    assert report.life_states[0].end_reason == "energy_depleted"
    assert report.life_states[0].tick == 1


def test_life_ends_on_max_ticks(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="max-ticks")
    try:
        report = runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=10)
    finally:
        runtime.monitoring.recorder.close()
    assert report.life_states[0].end_reason == "max_ticks_reached"
    assert report.life_states[0].tick == 10


def test_slow_memory_carryover_between_lives(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="carryover")
    observed = []
    agent = runtime.orchestrator.agent
    original_begin = agent.begin_episode
    original_end = agent.end_episode

    def begin_episode(obs):
        observed.append(float(agent.slow_memory.heatmaps[0, 0, 0, 0]))
        return original_begin(obs)

    def end_episode(summary):
        result = original_end(summary)
        if summary.episode_id == 1:
            agent.slow_memory.heatmaps[0, 0, 0, 0] = 7.0
        return result

    agent.begin_episode = begin_episode
    agent.end_episode = end_episode
    try:
        runtime.orchestrator.run("continuous_full", life_count=2, life_max_ticks=5)
    finally:
        runtime.monitoring.recorder.close()
    assert observed[:2] == [0.0, 7.0]


def test_slow_memory_reset_on_new_run(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="reset")
    observed = []
    agent = runtime.orchestrator.agent
    original_begin = agent.begin_episode
    original_end = agent.end_episode

    def begin_episode(obs):
        observed.append(float(agent.slow_memory.heatmaps[0, 0, 0, 0]))
        return original_begin(obs)

    def end_episode(summary):
        result = original_end(summary)
        agent.slow_memory.heatmaps[0, 0, 0, 0] = 9.0
        return result

    agent.begin_episode = begin_episode
    agent.end_episode = end_episode
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=5)
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=5)
    finally:
        runtime.monitoring.recorder.close()
    assert observed[:2] == [0.0, 0.0]


def test_artifacts_write_all_four_datasets(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="datasets")
    try:
        report = runtime.orchestrator.run("continuous_full", life_count=5, life_max_ticks=20)
    finally:
        runtime.monitoring.recorder.close()
    assert report.completed_lives == 5
    assert runtime.artifacts.life_summaries_path.exists()
    assert runtime.artifacts.window_metrics_path.exists()
    assert runtime.artifacts.event_metrics_path.exists()
    assert runtime.artifacts.series_metrics_path.exists()
    assert runtime.artifacts.slow_memory_path.exists()
    assert runtime.artifacts.manifest_path.exists()
    assert runtime.artifacts.series_metrics_path.read_text(encoding="utf-8").strip()


def test_artifacts_handle_empty_events(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="empty-events")
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=2)
    finally:
        runtime.monitoring.recorder.close()
    assert runtime.artifacts.event_metrics_path.read_text(encoding="utf-8") == ""


def test_continuous_full_smoke_500_ticks(tmp_path: Path):
    runtime = _build_life_runtime(tmp_path, run_id="smoke")
    try:
        report = runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=500)
    finally:
        runtime.monitoring.recorder.close()
    manifest = json.loads(runtime.artifacts.manifest_path.read_text(encoding="utf-8"))
    assert report.completed_lives == 1
    assert report.life_states[0].tick <= 500
    assert manifest["mode"] == "continuous_full"


def _build_life_runtime(
    tmp_path: Path,
    run_id: str,
    energy_start: int = 70,
    water_start: int = 70,
):
    config_path = _write_config(tmp_path, run_id, energy_start, water_start)
    settings = RuntimeSettings(
        artifacts_root=tmp_path / "artifacts",
        run_id=run_id,
        run_ablations=False,
        clean_artifacts=True,
    )
    return build_runtime(str(config_path), settings, mode="continuous_full")


def _write_config(tmp_path: Path, run_id: str, energy_start: int, water_start: int) -> Path:
    config_path = tmp_path / f"{run_id}.yaml"
    config_path.write_text(_config_text(run_id, energy_start, water_start), encoding="utf-8")
    return config_path


def _config_text(run_id: str, energy_start: int, water_start: int) -> str:
    return f"""run_id: {run_id}
enable_monitoring: false
run_ablations: false
train_episodes: 2
eval_episodes_seen: 0
eval_episodes_relocation: 0
body:
  energy_start: {energy_start}
  water_start: {water_start}
"""
