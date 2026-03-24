"""SagaStep — a single step with an optional compensating action."""

from __future__ import annotations
from typing import Any, Callable


class SagaStep:
    """Represents one step in a saga transaction.

    Parameters
    ----------
    name:       Unique identifier for this step.
    action:     Callable that performs the forward action.
    compensate: Optional callable that undoes the action on rollback.
    metadata:   Arbitrary key/value data attached to this step.
    """

    def __init__(
        self,
        name: str,
        action: Callable,
        compensate: Callable | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.name = name
        self.action = action
        self.compensate = compensate
        self.metadata: dict = metadata or {}
        self.status: str = "pending"
        self.result: Any = None
        self.error: str | None = None

    # ------------------------------------------------------------------
    # Forward execution
    # ------------------------------------------------------------------

    def run(self, *args, **kwargs) -> Any:
        """Execute the forward action.

        Sets ``status`` to ``"completed"`` on success or ``"failed"`` on error.
        Stores the return value in ``result`` and any exception message in ``error``.

        Raises
        ------
        Exception
            Re-raises whatever the underlying action raises so the orchestrating
            :class:`Saga` can trigger rollback.
        """
        try:
            self.result = self.action(*args, **kwargs)
            self.status = "completed"
            return self.result
        except Exception as exc:
            self.status = "failed"
            self.error = str(exc)
            raise

    # ------------------------------------------------------------------
    # Compensation / rollback
    # ------------------------------------------------------------------

    def rollback(self, *args, **kwargs) -> None:
        """Execute the compensating action if one was provided.

        Sets ``status`` to ``"rolled_back"`` after a successful compensation.
        If the compensation itself raises, the exception is **not** suppressed —
        the caller (usually :class:`Saga`) decides how to handle it.
        """
        if self.compensate is None:
            self.status = "rolled_back"
            return
        self.compensate(*args, **kwargs)
        self.status = "rolled_back"

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"SagaStep(name={self.name!r}, status={self.status!r})"
