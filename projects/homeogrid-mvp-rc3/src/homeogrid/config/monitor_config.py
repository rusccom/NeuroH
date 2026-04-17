"""Monitoring configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitorConfig:
    ui_hz: int = 5
    chart_history_sec: int = 120
    frame_buffer_size: int = 600
    raw_event_buffer_size: int = 4096
    sse_ping_sec: float = 2.0
    enable_debug_overlay: bool = False
    enable_blob3d: bool = True
    max_alerts_in_panel: int = 100
    bind_host: str = "127.0.0.1"
    bind_port: int = 8000
