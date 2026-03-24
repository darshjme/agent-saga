# Changelog

All notable changes to **agent-saga** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-24

### Added
- `SagaStep` — forward action + optional compensating action, lifecycle status tracking
- `Saga` — fluent step orchestrator with automatic reverse rollback on failure
- `Saga.step()` — decorator factory for inline step registration
- `Saga.rollback_completed()` — manual rollback trigger
- `SagaResult` — structured execution outcome with `to_dict()` serialization
- `SagaLog` — in-memory event recorder with per-saga filtering
- 31 pytest tests — 100% API coverage
- Zero runtime dependencies (Python 3.10+ stdlib only)
- Full README with flight/card/hotel booking example
