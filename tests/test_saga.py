"""Comprehensive test suite for agent-saga — 22+ tests."""

import pytest
from agent_saga import Saga, SagaStep, SagaResult, SagaLog


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_ok(name: str, value=None):
    """Return a SagaStep whose action succeeds and returns *value*."""
    def action():
        return value if value is not None else name
    return SagaStep(name=name, action=action)


def make_fail(name: str, msg: str = "boom"):
    """Return a SagaStep whose action always raises RuntimeError."""
    def action():
        raise RuntimeError(msg)
    return SagaStep(name=name, action=action)


# ---------------------------------------------------------------------------
# SagaStep tests
# ---------------------------------------------------------------------------

class TestSagaStep:
    def test_initial_status_is_pending(self):
        step = make_ok("s1")
        assert step.status == "pending"

    def test_run_sets_completed_status(self):
        step = make_ok("s1", value=42)
        result = step.run()
        assert step.status == "completed"
        assert result == 42
        assert step.result == 42

    def test_run_stores_return_value(self):
        step = SagaStep("s", action=lambda: {"key": "val"})
        step.run()
        assert step.result == {"key": "val"}

    def test_run_sets_failed_status_on_error(self):
        step = make_fail("s1", "oops")
        with pytest.raises(RuntimeError, match="oops"):
            step.run()
        assert step.status == "failed"
        assert step.error == "oops"

    def test_rollback_without_compensate_sets_rolled_back(self):
        step = make_ok("s1")
        step.run()
        step.rollback()
        assert step.status == "rolled_back"

    def test_rollback_calls_compensate(self):
        called = []
        step = SagaStep("s", action=lambda: None, compensate=lambda: called.append(1))
        step.run()
        step.rollback()
        assert called == [1]
        assert step.status == "rolled_back"

    def test_metadata_stored(self):
        step = SagaStep("s", action=lambda: None, metadata={"service": "flight"})
        assert step.metadata["service"] == "flight"

    def test_metadata_defaults_to_empty_dict(self):
        step = SagaStep("s", action=lambda: None)
        assert step.metadata == {}

    def test_run_passes_args_to_action(self):
        step = SagaStep("s", action=lambda x, y: x + y)
        assert step.run(3, 4) == 7

    def test_rollback_passes_args_to_compensate(self):
        received = []
        step = SagaStep("s", action=lambda: None, compensate=lambda x: received.append(x))
        step.run()
        step.rollback(99)
        assert received == [99]


# ---------------------------------------------------------------------------
# SagaResult tests
# ---------------------------------------------------------------------------

class TestSagaResult:
    def test_to_dict_success(self):
        r = SagaResult(success=True, completed_steps=["a", "b"])
        d = r.to_dict()
        assert d["success"] is True
        assert d["completed_steps"] == ["a", "b"]
        assert d["failed_step"] is None
        assert d["rolled_back"] == []
        assert d["error"] is None

    def test_to_dict_failure(self):
        r = SagaResult(
            success=False,
            completed_steps=["a"],
            failed_step="b",
            rolled_back=["a"],
            error="boom",
        )
        d = r.to_dict()
        assert d["success"] is False
        assert d["failed_step"] == "b"
        assert d["rolled_back"] == ["a"]
        assert d["error"] == "boom"


# ---------------------------------------------------------------------------
# SagaLog tests
# ---------------------------------------------------------------------------

class TestSagaLog:
    def test_record_and_events(self):
        log = SagaLog()
        log.record("saga1", "started")
        assert len(log.events) == 1
        assert log.events[0]["event"] == "started"

    def test_for_saga_filters_correctly(self):
        log = SagaLog()
        log.record("saga1", "e1")
        log.record("saga2", "e2")
        log.record("saga1", "e3")
        assert len(log.for_saga("saga1")) == 2
        assert len(log.for_saga("saga2")) == 1

    def test_record_with_step_and_data(self):
        log = SagaLog()
        log.record("s", "step_started", step="flight", data={"key": 1})
        e = log.events[0]
        assert e["step"] == "flight"
        assert e["data"] == {"key": 1}

    def test_clear(self):
        log = SagaLog()
        log.record("s", "e")
        log.clear()
        assert len(log.events) == 0

    def test_len(self):
        log = SagaLog()
        log.record("s", "e1")
        log.record("s", "e2")
        assert len(log) == 2

    def test_events_returns_copy(self):
        log = SagaLog()
        log.record("s", "e")
        events = log.events
        events.clear()
        assert len(log.events) == 1  # original unaffected

    def test_ts_is_float(self):
        log = SagaLog()
        log.record("s", "e")
        assert isinstance(log.events[0]["ts"], float)


# ---------------------------------------------------------------------------
# Saga orchestration tests
# ---------------------------------------------------------------------------

class TestSagaExecution:
    def test_all_steps_succeed(self):
        saga = Saga("test")
        saga.add(SagaStep("a", action=lambda: 1))
        saga.add(SagaStep("b", action=lambda: 2))
        result = saga.execute()
        assert result.success is True
        assert result.completed_steps == ["a", "b"]
        assert result.failed_step is None
        assert result.rolled_back == []
        assert result.results == {"a": 1, "b": 2}

    def test_failure_triggers_rollback_in_reverse(self):
        rollback_order = []
        saga = Saga("test")
        saga.add(SagaStep("a", action=lambda: "a", compensate=lambda: rollback_order.append("a")))
        saga.add(SagaStep("b", action=lambda: "b", compensate=lambda: rollback_order.append("b")))
        saga.add(SagaStep("c", action=lambda: (_ for _ in ()).throw(RuntimeError("c-fail"))))
        result = saga.execute()
        assert result.success is False
        assert result.failed_step == "c"
        assert result.rolled_back == ["b", "a"]
        assert rollback_order == ["b", "a"]

    def test_flight_card_hotel_scenario(self):
        """The canonical booking saga — hotel fails, card+flight are refunded."""
        log = []

        def book_flight(): log.append("book_flight"); return "FL123"
        def cancel_flight(): log.append("cancel_flight")
        def charge_card(): log.append("charge_card"); return "ch_abc"
        def refund_card(): log.append("refund_card")
        def book_hotel(): raise RuntimeError("Hotel unavailable")

        saga = Saga("booking")
        saga.add(SagaStep("flight", book_flight, cancel_flight))
        saga.add(SagaStep("card",   charge_card,  refund_card))
        saga.add(SagaStep("hotel",  book_hotel))

        result = saga.execute()

        assert result.success is False
        assert result.failed_step == "hotel"
        assert result.completed_steps == ["flight", "card"]
        assert result.rolled_back == ["card", "flight"]
        assert "cancel_flight" in log
        assert "refund_card" in log

    def test_fluent_add_returns_saga(self):
        saga = Saga("s")
        returned = saga.add(SagaStep("a", action=lambda: None))
        assert returned is saga

    def test_empty_saga_succeeds(self):
        result = Saga("empty").execute()
        assert result.success is True
        assert result.completed_steps == []

    def test_rollback_completed_manual(self):
        rolled = []
        saga = Saga("s")
        saga.add(SagaStep("a", action=lambda: None, compensate=lambda: rolled.append("a")))
        saga.add(SagaStep("b", action=lambda: None, compensate=lambda: rolled.append("b")))
        saga.execute()
        # All steps completed — now manually trigger rollback
        names = saga.rollback_completed()
        assert names == ["b", "a"]
        assert rolled == ["b", "a"]

    def test_decorator_factory(self):
        saga = Saga("decor")
        cancel_called = []

        def cancel(): cancel_called.append(True)

        @saga.step("book", compensate=cancel)
        def book():
            return "booked"

        result = saga.execute()
        assert result.success is True
        assert result.results["book"] == "booked"
        # Decorated function still callable
        assert book() == "booked"

    def test_log_attached_to_saga(self):
        saga = Saga("logged")
        saga.add(SagaStep("x", action=lambda: 42))
        saga.execute()
        events = saga.log.for_saga("logged")
        event_names = [e["event"] for e in events]
        assert "saga_started" in event_names
        assert "step_completed" in event_names
        assert "saga_completed" in event_names

    def test_external_log_shared(self):
        shared_log = SagaLog()
        saga1 = Saga("s1", log=shared_log)
        saga2 = Saga("s2", log=shared_log)
        saga1.add(SagaStep("a", action=lambda: None)).execute()
        saga2.add(SagaStep("b", action=lambda: None)).execute()
        assert len(shared_log.for_saga("s1")) > 0
        assert len(shared_log.for_saga("s2")) > 0

    def test_steps_property(self):
        saga = Saga("s")
        step = SagaStep("a", action=lambda: None)
        saga.add(step)
        assert saga.steps == [step]
        # Mutation of returned list doesn't affect saga
        saga.steps.clear()
        assert len(saga.steps) == 1

    def test_error_message_preserved_in_result(self):
        saga = Saga("s")
        saga.add(SagaStep("x", action=lambda: (_ for _ in ()).throw(ValueError("bad input"))))
        result = saga.execute()
        assert result.error == "bad input"

    def test_compensate_error_does_not_stop_other_rollbacks(self):
        """If one compensate raises, remaining compensations still execute."""
        log = []
        def bad_compensate(): raise RuntimeError("compensate failed")
        def good_compensate(): log.append("good")

        saga = Saga("s")
        saga.add(SagaStep("a", action=lambda: None, compensate=good_compensate))
        saga.add(SagaStep("b", action=lambda: None, compensate=bad_compensate))
        saga.add(SagaStep("c", action=lambda: (_ for _ in ()).throw(RuntimeError("fail"))))
        result = saga.execute()
        # "a" was completed but "b"'s rollback failed — "a" should still be attempted
        assert "good" in log
