from fastapi.testclient import TestClient

from homeoorganism.app.run import build_runtime
from homeoorganism.monitoring.web.api import create_monitor_app


def test_single_episode_runs(runtime):
    summary = runtime.orchestrator.run_single_episode(123)
    assert summary.steps > 0


def test_monitor_api_bootstrap_and_pages():
    runtime = build_runtime("configs/full.yaml")
    app = create_monitor_app(
        runtime.monitoring,
        runtime.control_port,
        "src/homeoorganism/monitoring/web/static",
    )
    client = TestClient(app)
    assert client.get("/monitor").status_code == 200
    assert client.get("/api/monitor/bootstrap").status_code == 200


def test_command_endpoint_accepts_pause():
    runtime = build_runtime("configs/full.yaml")
    app = create_monitor_app(
        runtime.monitoring,
        runtime.control_port,
        "src/homeoorganism/monitoring/web/static",
    )
    client = TestClient(app)
    response = client.post("/api/monitor/command", json={"command": "pause"})
    assert response.status_code == 200
    assert response.json()["accepted"] is True
