<div align="center">
<img src="assets/hero.svg" width="100%"/>
</div>

# agent-saga

**Distributed saga pattern for multi-agent systems — automatic rollback without a global coordinator**

[![PyPI version](https://img.shields.io/pypi/v/agent-saga?color=purple&style=flat-square)](https://pypi.org/project/agent-saga/) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org) [![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE) [![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](#)

---

## The Problem

Without the saga pattern, a distributed transaction that fails halfway leaves the system in an inconsistent state. Partial writes with no compensating logic produce data corruption that is exponentially harder to clean up than to prevent.

## Installation

```bash
pip install agent-saga
```

## Quick Start

```python
from agent_saga import SagaLog, SagaResult, Saga

# Initialise
instance = SagaLog(name="my_agent")

# Use
# see API reference below
print(result)
```

## API Reference

### `SagaLog`

```python
class SagaLog:
    """Records saga lifecycle events.
    def __init__(self) -> None:
    def record(
    def events(self) -> list[dict]:
        """Return all recorded events (read-only copy)."""
    def for_saga(self, saga_name: str) -> list[dict]:
        """Return only the events that belong to *saga_name*."""
```

### `SagaResult`

```python
class SagaResult:
    """Holds the outcome of a Saga execution."""
    def to_dict(self) -> dict:
```

### `Saga`

```python
class SagaLog:
    """Records saga lifecycle events.
    def __init__(self) -> None:
    def record(
    def events(self) -> list[dict]:
        """Return all recorded events (read-only copy)."""
    def for_saga(self, saga_name: str) -> list[dict]:
        """Return only the events that belong to *saga_name*."""
```


## How It Works

### Flow

```mermaid
flowchart LR
    A[User Code] -->|create| B[SagaLog]
    B -->|configure| C[SagaResult]
    C -->|execute| D{Success?}
    D -->|yes| E[Return Result]
    D -->|no| F[Error Handler]
    F --> G[Fallback / Retry]
    G --> C
```

### Sequence

```mermaid
sequenceDiagram
    participant App
    participant SagaLog
    participant SagaResult

    App->>+SagaLog: initialise()
    SagaLog->>+SagaResult: configure()
    SagaResult-->>-SagaLog: ready
    App->>+SagaLog: run(context)
    SagaLog->>+SagaResult: execute(context)
    SagaResult-->>-SagaLog: result
    SagaLog-->>-App: WorkflowResult
```

## Philosophy

> The *Ramayana* is itself a saga of compensating transactions — every exile balanced by a return.

---

*Part of the [arsenal](https://github.com/darshjme/arsenal) — production stack for LLM agents.*

*Built by [Darshankumar Joshi](https://github.com/darshjme), Gujarat, India.*
