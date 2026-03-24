"""SagaLog — lightweight event recorder for debugging and replay."""

from __future__ import annotations
import time
from typing import Any


class SagaLog:
    """Records saga lifecycle events.

    All events are kept in memory as plain dicts with the shape::

        {
            "ts":        float,           # Unix timestamp
            "saga":      str,             # saga name
            "event":     str,             # e.g. "step_started"
            "step":      str | None,      # step name (if applicable)
            "data":      dict | None,     # arbitrary payload
        }
    """

    def __init__(self) -> None:
        self._events: list[dict] = []

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def record(
        self,
        saga_name: str,
        event: str,
        step: str | None = None,
        data: dict | None = None,
    ) -> None:
        """Append one event to the log."""
        self._events.append(
            {
                "ts": time.time(),
                "saga": saga_name,
                "event": event,
                "step": step,
                "data": data,
            }
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @property
    def events(self) -> list[dict]:
        """Return all recorded events (read-only copy)."""
        return list(self._events)

    def for_saga(self, saga_name: str) -> list[dict]:
        """Return only the events that belong to *saga_name*."""
        return [e for e in self._events if e["saga"] == saga_name]

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Discard all recorded events."""
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SagaLog(events={len(self._events)})"
