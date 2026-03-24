# agent-saga

**Distributed saga pattern for multi-agent systems** — automatic rollback without a global coordinator.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## The Problem

When a multi-step agent operation partially succeeds:

```
book flight ✓  →  charge card ✓  →  book hotel ✗
```

…you need **compensating actions** to undo the completed steps (refund card, cancel flight).
The Saga pattern solves distributed transaction rollback **without a global coordinator**.

---

## Install

```bash
pip install agent-saga
```

---

## Quickstart — Flight / Card / Hotel Booking

```python
from agent_saga import Saga, SagaStep

# --- forward actions ---
def book_flight():
    print("✈  Flight FL123 booked")
    return "FL123"

def charge_card():
    print("💳  Card charged $499")
    return "ch_abc123"

def book_hotel():
    # Suppose the hotel is unavailable
    raise RuntimeError("Hotel fully booked")

# --- compensating actions ---
def cancel_flight():
    print("✈  Flight FL123 cancelled")

def refund_card():
    print("💳  Card refunded $499")

# --- build the saga ---
saga = (
    Saga("travel-booking")
    .add(SagaStep("flight", book_flight,  cancel_flight))
    .add(SagaStep("card",   charge_card,  refund_card))
    .add(SagaStep("hotel",  book_hotel))          # no compensate needed — it never ran
)

result = saga.execute()

print(result.success)          # False
print(result.failed_step)      # "hotel"
print(result.completed_steps)  # ["flight", "card"]
print(result.rolled_back)      # ["card", "flight"]  ← reverse order ✓
```

**Output:**
```
✈  Flight FL123 booked
💳  Card charged $499
💳  Card refunded $499
✈  Flight FL123 cancelled
```

---

## Core API

### `SagaStep`

```python
SagaStep(
    name: str,
    action: callable,
    compensate: callable = None,
    metadata: dict = None,
)
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique step identifier |
| `status` | `str` | `"pending"` → `"completed"` / `"failed"` / `"rolled_back"` |
| `result` | `any` | Return value of `action` |
| `error` | `str\|None` | Exception message if `action` raised |

```python
step.run(*args, **kwargs)       # execute forward action
step.rollback(*args, **kwargs)  # execute compensating action
```

---

### `Saga`

```python
saga = Saga("name")
saga.add(step)           # fluent — returns saga
result = saga.execute()  # run all steps; auto-rollback on failure
saga.rollback_completed()  # manual rollback of all completed steps
```

**Decorator factory:**

```python
saga = Saga("order")

@saga.step("reserve-inventory", compensate=release_inventory)
def reserve():
    return db.reserve(sku="ITEM-9")
```

---

### `SagaResult`

```python
result.success           # bool
result.completed_steps   # list[str]
result.failed_step       # str | None
result.rolled_back       # list[str]
result.results           # dict[str, any]  — per-step return values
result.error             # str | None

result.to_dict()         # serialize to plain dict
```

---

### `SagaLog`

```python
log = SagaLog()
saga = Saga("checkout", log=log)

log.events              # all recorded events
log.for_saga("checkout")  # filter by saga name
log.record("checkout", "custom_event", step="pay", data={"amount": 99})
```

Each event is a `dict`:
```python
{
    "ts":    1711234567.89,   # Unix timestamp
    "saga":  "checkout",
    "event": "step_completed",
    "step":  "pay",
    "data":  {"result": "..."},
}
```

---

## Advanced Usage

### Shared context via `execute()` args

```python
def book_flight(ctx):
    ctx["flight_id"] = "FL123"

def cancel_flight(ctx):
    del ctx["flight_id"]

ctx = {}
saga = Saga("trip")
saga.add(SagaStep("flight", book_flight, cancel_flight))
saga.execute(ctx)
```

### Shared log across multiple sagas

```python
from agent_saga import SagaLog, Saga, SagaStep

log = SagaLog()
saga_a = Saga("checkout", log=log)
saga_b = Saga("refund",   log=log)

# Both sagas write to the same log
log.for_saga("checkout")   # events for checkout only
log.for_saga("refund")     # events for refund only
```

---

## Design Principles

- **Zero dependencies** — pure Python 3.10+ stdlib only
- **Always returns** — `execute()` never propagates exceptions
- **Best-effort rollback** — if a compensating action raises, remaining rollbacks still proceed
- **Reverse order** — rollbacks always happen newest-first
- **Immutable result** — `SagaResult` is a dataclass; safe to store/serialize

---

## License

MIT — see [LICENSE](LICENSE).
