"""Buffered JSONL recorder."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Thread

from homeoorganism.monitoring.domain.enums import StreamEventType


@dataclass
class PersistedFrameState:
    seen_count: int = 0
    last_payload: dict | None = None
    last_written_step: int | None = None


@dataclass
class SessionRecorder:
    root_dir: str
    max_queue: int
    frame_stride: int = 5
    _frames: Queue = field(init=False)
    _important: Queue = field(init=False)
    _frame_states: dict[tuple[str, int], PersistedFrameState] = field(init=False, default_factory=dict)
    _stop: Event = field(default_factory=Event)
    _worker: Thread = field(init=False)

    def __post_init__(self) -> None:
        self._frames = Queue(maxsize=self.max_queue)
        self._important = Queue(maxsize=self.max_queue)
        self._worker = Thread(target=self._run, daemon=True)
        self._worker.start()

    def record(self, run_id: str, episode_id: int, event_type: StreamEventType, payload) -> None:
        if event_type == StreamEventType.FRAME:
            self._record_frame(run_id, episode_id, payload)
            return
        if event_type == StreamEventType.SUMMARY:
            self._flush_last_frame(run_id, episode_id)
            self._frame_states.pop((run_id, episode_id), None)
        self._enqueue_important(run_id, episode_id, self._record_payload(event_type, payload))

    def close(self) -> None:
        self._flush_open_frames()
        self._stop.set()
        self._worker.join()

    def _record_frame(self, run_id: str, episode_id: int, payload: dict) -> None:
        state = self._frame_states.setdefault((run_id, episode_id), PersistedFrameState())
        state.seen_count += 1
        state.last_payload = payload
        if state.seen_count == 1 or state.seen_count % self.frame_stride == 0:
            self._enqueue_frame(run_id, episode_id, payload, state)

    def _run(self) -> None:
        while not self._stop.is_set() or self._has_pending_records():
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

    def _has_pending_records(self) -> bool:
        return not self._frames.empty() or not self._important.empty()

    def _discard_one_frame(self) -> None:
        try:
            self._frames.get_nowait()
        except Empty:
            return

    def _enqueue_frame(self, run_id: str, episode_id: int, payload: dict, state: PersistedFrameState) -> None:
        step_idx = self._step_idx(payload)
        if step_idx == state.last_written_step:
            return
        state.last_written_step = step_idx
        self._enqueue_important(run_id, episode_id, self._record_payload(StreamEventType.FRAME, payload))

    def _enqueue_important(self, run_id: str, episode_id: int, record: dict) -> None:
        while True:
            try:
                self._important.put((run_id, episode_id, record), timeout=0.1)
                return
            except Full:
                if self._stop.is_set():
                    return

    def _flush_last_frame(self, run_id: str, episode_id: int) -> None:
        state = self._frame_states.get((run_id, episode_id))
        if state is None or state.last_payload is None:
            return
        self._enqueue_frame(run_id, episode_id, state.last_payload, state)

    def _flush_open_frames(self) -> None:
        for run_id, episode_id in list(self._frame_states):
            self._flush_last_frame(run_id, episode_id)
            self._frame_states.pop((run_id, episode_id), None)

    def _record_payload(self, event_type: StreamEventType, payload) -> dict:
        return {"type": event_type.value, "payload": payload}

    def _step_idx(self, payload: dict) -> int | None:
        world = payload.get("world")
        if isinstance(world, dict):
            return world.get("step_idx")
        return None
