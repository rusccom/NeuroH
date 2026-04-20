from pathlib import Path

from fastapi.testclient import TestClient

from homeoorganism.app.run import build_runtime
from homeoorganism.app.runtime_settings import RuntimeSettings
from homeoorganism.monitoring.domain.dto import StepSnapshot
from homeoorganism.monitoring.domain.life_snapshot import LifeSnapshot
from homeoorganism.monitoring.web.api import create_monitor_app


def test_monitoring_uses_life_snapshot_for_continuous_mode(tmp_path: Path):
    runtime = _build_runtime(tmp_path, "continuous_full", "continuous")
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=20)
    finally:
        runtime.monitoring.recorder.close()
    assert isinstance(runtime.monitoring.latest_snapshot(), LifeSnapshot)


def test_monitoring_keeps_step_snapshot_for_episodic_mode(tmp_path: Path):
    runtime = _build_runtime(tmp_path, "episodic_full", "episodic")
    try:
        runtime.orchestrator.run_single_episode(123)
    finally:
        runtime.monitoring.recorder.close()
    assert isinstance(runtime.monitoring.latest_snapshot(), StepSnapshot)
    assert not isinstance(runtime.monitoring.latest_snapshot(), LifeSnapshot)


def test_snapshot_endpoint_returns_life_snapshot_json(tmp_path: Path):
    runtime = _build_runtime(tmp_path, "continuous_full", "api")
    try:
        runtime.orchestrator.run("continuous_full", life_count=1, life_max_ticks=20)
        app = create_monitor_app(
            runtime.monitoring,
            runtime.control_port,
            "src/homeoorganism/monitoring/web/static",
        )
        client = TestClient(app)
        response = client.get("/snapshot")
    finally:
        runtime.monitoring.recorder.close()
    assert response.status_code == 200
    payload = response.json()["snapshot"]
    assert payload["life_id"] == 1
    assert payload["current_tick"] <= 20


def _build_runtime(tmp_path: Path, mode: str, run_id: str):
    config_path = tmp_path / f"{run_id}.yaml"
    config_path.write_text(_config_text(run_id, mode), encoding="utf-8")
    settings = RuntimeSettings(
        artifacts_root=tmp_path / "artifacts",
        run_id=run_id,
        run_ablations=False,
        clean_artifacts=True,
    )
    return build_runtime(str(config_path), settings, mode=mode)


def _config_text(run_id: str, mode: str) -> str:
    return f"""run_id: {run_id}
mode: {mode}
enable_monitoring: false
run_ablations: false
train_episodes: 0
eval_episodes_seen: 1
eval_episodes_relocation: 0
lives_per_seed: 1
life_max_ticks: 20
"""
