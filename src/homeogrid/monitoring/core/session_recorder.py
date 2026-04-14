"""Buffered JSONL recorder."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Thread

from homeogrid.monitoring.domain.enums import StreamEventType


@dataclass
class SessionRecorder:
    root_dir: str
    max_queue: int
    _frames: Queue = field(init=False)
    _important: Queue = field(init=False)
    _stop: Event = field(default_factory=Event)
    _worker: Thread = field(init=False)

    def __post_init__(self) -> None:
        self._frames = Queue(maxsize=self.max_queue)
        self._important = Queue(maxsize=self.max_queue)
        self._worker = Thread(target=self._run, daemon=True)
        self._worker.start()

    def record(self, run_id: str, episode_id: int, event_type: StreamEventType, payload) -> None:
        record = {"type": event_type.value, "payload": payload}
        queue = self._frames if event_type == StreamEventType.FRAME else self._important
        if event_type == StreamEventType.FRAME and queue.full():
            return
        try:
            queue.put_nowait((run_id, episode_id, record))
        except Full:
            self._discard_one_frame()
            try:
                queue.put_nowait((run_id, episode_id, record))
            except Full:
                return

    def close(self) -> None:
        self._stop.set()
        self._worker.join(timeout=1)

    def _run(self) -> None:
        while not self._stop.is_set():
            item = self._next_item()
            if item is None:
                continue
            run_id, episode_id, record = item
            self._append(run_id, episode_id, record)

    def _next_item(self):
        for queue in (self._important, self._frames):
            try:
                return queue.get(timeout=0.1)
            except Empty:
                continue
        return None

    def _append(self, run_id: str, episode_id: int, record: dict) -> None:
        path = Path(self.root_dir) / run_id / f"{episode_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _discard_one_frame(self) -> None:
        try:
            self._frames.get_nowait()
        except Empty:
            return
