"""Saga — orchestrates SagaSteps with automatic rollback on failure."""

from __future__ import annotations
import functools
from typing import Any, Callable

from .log import SagaLog
from .result import SagaResult
from .step import SagaStep


class Saga:
    """Orchestrates a sequence of :class:`SagaStep` objects.

    On failure the saga automatically rolls back all *completed* steps in
    **reverse** order before returning a :class:`SagaResult`.

    Parameters
    ----------
    name: Human-readable name used in logging and result objects.

    Example
    -------
    >>> saga = Saga("booking")
    >>> saga.add(SagaStep("flight", book_flight, cancel_flight))
    >>> saga.add(SagaStep("card",   charge_card,  refund_card))
    >>> saga.add(SagaStep("hotel",  book_hotel,   cancel_hotel))
    >>> result = saga.execute()
    >>> result.success
    False
    >>> result.rolled_back
    ['card', 'flight']
    """

    def __init__(self, name: str, log: SagaLog | None = None) -> None:
        self.name = name
        self._steps: list[SagaStep] = []
        self._log: SagaLog = log if log is not None else SagaLog()

    # ------------------------------------------------------------------
    # Builder API
    # ------------------------------------------------------------------

    def add(self, step: SagaStep) -> "Saga":
        """Append *step* and return *self* for fluent chaining."""
        self._steps.append(step)
        return self

    def step(
        self,
        name: str,
        compensate: Callable | None = None,
        metadata: dict | None = None,
    ) -> Callable:
        """Decorator factory that wraps a function as a :class:`SagaStep`.

        Usage::

            @saga.step("flight", compensate=cancel_flight)
            def book_flight():
                ...

        The decorated function is added to the saga immediately and the
        *original* function is returned unchanged (so it can also be called
        independently).
        """

        def decorator(fn: Callable) -> Callable:
            saga_step = SagaStep(
                name=name,
                action=fn,
                compensate=compensate,
                metadata=metadata,
            )
            self.add(saga_step)

            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)

            return wrapper

        return decorator

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, *args, **kwargs) -> SagaResult:
        """Run all steps in order.

        If any step raises, all previously *completed* steps are rolled back in
        reverse order.  The method always returns a :class:`SagaResult` — it
        never propagates exceptions to the caller.

        Parameters
        ----------
        *args / **kwargs:
            Forwarded to **every** step's ``run()`` and ``rollback()`` calls.
            Useful for shared context objects (e.g. a database session).
        """
        completed: list[SagaStep] = []
        results: dict[str, Any] = {}

        self._log.record(self.name, "saga_started")

        for current_step in self._steps:
            self._log.record(self.name, "step_started", step=current_step.name)
            try:
                value = current_step.run(*args, **kwargs)
                results[current_step.name] = value
                completed.append(current_step)
                self._log.record(
                    self.name,
                    "step_completed",
                    step=current_step.name,
                    data={"result": repr(value)},
                )
            except Exception as exc:
                self._log.record(
                    self.name,
                    "step_failed",
                    step=current_step.name,
                    data={"error": str(exc)},
                )
                # Roll back all previously completed steps (reverse order)
                rolled_back = self._rollback_steps(completed, *args, **kwargs)

                self._log.record(self.name, "saga_failed")
                return SagaResult(
                    success=False,
                    completed_steps=[s.name for s in completed],
                    failed_step=current_step.name,
                    rolled_back=rolled_back,
                    results=results,
                    error=str(exc),
                )

        self._log.record(self.name, "saga_completed")
        return SagaResult(
            success=True,
            completed_steps=[s.name for s in self._steps],
            failed_step=None,
            rolled_back=[],
            results=results,
            error=None,
        )

    def rollback_completed(self, *args, **kwargs) -> list[str]:
        """Manually roll back every step that is currently ``"completed"``.

        Returns the list of step names that were rolled back.
        """
        completed = [s for s in self._steps if s.status == "completed"]
        return self._rollback_steps(completed, *args, **kwargs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rollback_steps(
        self, steps: list[SagaStep], *args, **kwargs
    ) -> list[str]:
        """Roll back *steps* in reverse order; return names of rolled-back steps."""
        rolled_back: list[str] = []
        for step in reversed(steps):
            self._log.record(self.name, "step_rollback_started", step=step.name)
            try:
                step.rollback(*args, **kwargs)
                rolled_back.append(step.name)
                self._log.record(
                    self.name, "step_rolled_back", step=step.name
                )
            except Exception as exc:
                self._log.record(
                    self.name,
                    "step_rollback_failed",
                    step=step.name,
                    data={"error": str(exc)},
                )
                # Best-effort: continue rolling back remaining steps
        return rolled_back

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def log(self) -> SagaLog:
        """The :class:`SagaLog` attached to this saga."""
        return self._log

    @property
    def steps(self) -> list[SagaStep]:
        """Ordered list of registered steps (read-only copy)."""
        return list(self._steps)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Saga(name={self.name!r}, steps={len(self._steps)})"
