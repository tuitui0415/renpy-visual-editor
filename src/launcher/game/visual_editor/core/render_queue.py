"""Thread-safe debounce state for automatic stage rendering."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class QueuedStageRender:
    generation: int
    payload: object


class StageRenderCoordinator:
    def __init__(self, debounce_seconds: float = 0.3):
        self.debounce_seconds = debounce_seconds
        self._lock = threading.Lock()
        self._latest_generation = 0
        self._pending: Optional[QueuedStageRender] = None
        self._due_at = 0.0
        self._active_generation: Optional[int] = None

    def submit(self, payload: object, now: float) -> int:
        with self._lock:
            self._latest_generation += 1
            self._pending = QueuedStageRender(self._latest_generation, payload)
            self._due_at = now + self.debounce_seconds
            return self._latest_generation

    def claim(self, now: float) -> Optional[QueuedStageRender]:
        with self._lock:
            if self._active_generation is not None or self._pending is None or now < self._due_at:
                return None
            request = self._pending
            self._pending = None
            self._active_generation = request.generation
            return request

    def complete(self, generation: int) -> bool:
        with self._lock:
            if self._active_generation != generation:
                return False
            self._active_generation = None
            return generation == self._latest_generation

    @property
    def has_pending(self) -> bool:
        with self._lock:
            return self._pending is not None

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active_generation is not None
