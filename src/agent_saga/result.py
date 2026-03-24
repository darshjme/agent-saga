"""SagaResult — execution outcome of a Saga."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SagaResult:
    """Holds the outcome of a Saga execution."""

    success: bool
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str | None = None
    rolled_back: list[str] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "completed_steps": self.completed_steps,
            "failed_step": self.failed_step,
            "rolled_back": self.rolled_back,
            "results": self.results,
            "error": self.error,
        }
