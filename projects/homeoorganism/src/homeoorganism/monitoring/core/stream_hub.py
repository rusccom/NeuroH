"""SSE subscriber hub."""

from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Full, Queue
from threading import Lock

from homeoorganism.monitoring.domain.enums import StreamEventType


@dataclass
class StreamHub:
    subscriber_size: int = 128
    _subscribers: list[Queue] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock)

    def subscribe(self) -> Queue:
        queue = Queue(maxsize=self.subscriber_size)
        with self._lock:
            self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: Queue) -> None:
        with self._lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)

    def publish(self, event_type: StreamEventType, payload) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for queue in subscribers:
            self._publish_one(queue, event_type, payload)

    def _publish_one(self, queue: Queue, event_type: StreamEventType, payload) -> None:
        try:
            queue.put_nowait((event_type, payload))
        except Full:
            if event_type == StreamEventType.FRAME:
                self._drop_one(queue)
                self._safe_put(queue, event_type, payload)
                return
            self._drop_frames(queue)
            self._safe_put(queue, event_type, payload)

    def _drop_one(self, queue: Queue) -> None:
        try:
            queue.get_nowait()
        except Empty:
            return

    def _drop_frames(self, queue: Queue) -> None:
        buffered = []
        while True:
            try:
                item = queue.get_nowait()
                if item[0] == StreamEventType.FRAME:
                    continue
                buffered.append(item)
            except Empty:
                break
        for item in buffered:
            self._safe_put(queue, item[0], item[1])

    def _safe_put(self, queue: Queue, event_type, payload) -> None:
        try:
            queue.put_nowait((event_type, payload))
        except Full:
            return
