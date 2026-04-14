"""FastAPI application for monitoring."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from queue import Empty

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from homeogrid.monitoring.domain.dto import OperatorCommand
from homeogrid.monitoring.domain.enums import OperatorCommandType, StreamEventType


def create_monitor_app(monitoring, control_port, static_dir: str) -> FastAPI:
    app = FastAPI(title="HomeoGrid Monitor")
    router = APIRouter()
    static_path = Path(static_dir)
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    _add_page_routes(router, static_path)
    _add_api_routes(router, monitoring, control_port)
    app.include_router(router)
    return app


def _add_page_routes(router: APIRouter, static_path: Path) -> None:
    @router.get("/monitor")
    def monitor_page():
        return FileResponse(static_path / "index.html")

    @router.get("/replay/{run_id}/{episode_id}")
    def replay_page(run_id: str, episode_id: int):
        return FileResponse(static_path / "replay.html")


def _add_api_routes(router: APIRouter, monitoring, control_port) -> None:
    @router.get("/api/monitor/bootstrap")
    def bootstrap():
        return JSONResponse(_json_ready(monitoring.bootstrap()))

    @router.get("/api/monitor/stream")
    async def stream(request: Request):
        return StreamingResponse(_stream_events(request, monitoring), media_type="text/event-stream")

    @router.post("/api/monitor/command")
    def command(command: OperatorCommand):
        command_type = OperatorCommandType(command.command_type)
        accepted, message = _dispatch(control_port, command_type, command.enabled)
        return {"accepted": accepted, "run_state": control_port.get_run_state(), "message": message}

    @router.get("/api/monitor/history/{run_id}/{episode_id}")
    def history(run_id: str, episode_id: int):
        return JSONResponse(_json_ready(monitoring.history(run_id, episode_id)))


def _dispatch(control_port, command_type: OperatorCommandType, enabled: bool | None):
    if command_type == OperatorCommandType.PAUSE:
        return control_port.pause(), "Simulation paused"
    if command_type == OperatorCommandType.RESUME:
        return control_port.resume(), "Simulation resumed"
    if command_type == OperatorCommandType.RESET_EPISODE:
        return control_port.reset_episode(), "Episode reset requested"
    if command_type == OperatorCommandType.SAVE_SNAPSHOT:
        path = control_port.save_snapshot()
        return path is not None, "Snapshot saved" if path else "No snapshot available"
    return control_port.toggle_debug(enabled), "Debug mode updated"


def _sse(event_name: str, payload: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(_json_ready(payload), ensure_ascii=False)}\n\n"


def _json_ready(value):
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


async def _stream_events(request: Request, monitoring):
    queue = monitoring.stream_hub.subscribe()
    latest = monitoring.frame_buffer.latest()
    try:
        if latest is not None:
            yield _sse(StreamEventType.FRAME.value, latest.model_dump())
        while True:
            if await request.is_disconnected():
                break
            yield await _next_stream_payload(queue)
    finally:
        monitoring.stream_hub.unsubscribe(queue)


async def _next_stream_payload(queue) -> str:
    try:
        event_type, payload = await asyncio.to_thread(queue.get, True, 2.0)
        return _sse(event_type.value, payload)
    except Empty:
        return _sse(StreamEventType.HEARTBEAT.value, {"ok": True})
