"""Monitoring publisher interface."""

from __future__ import annotations

from typing import Protocol


class TelemetryPublisher(Protocol):
    def publish_step(self, snapshot) -> None: ...

    def publish_event(self, event) -> None: ...

    def publish_episode_end(self, summary) -> None: ...


class NullTelemetryPublisher:
    def publish_step(self, snapshot) -> None:
        return None

    def publish_event(self, event) -> None:
        return None

    def publish_episode_end(self, summary) -> None:
        return None
