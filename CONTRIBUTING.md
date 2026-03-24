# Contributing to agent-saga

Thank you for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/darshjme-codes/agent-saga
cd agent-saga
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

All 31 tests must pass before opening a PR.

## Guidelines

- **Zero dependencies** — the library must stay pure Python 3.10+ stdlib.
- **Test first** — add or update tests for every change.
- **Type hints** — use `from __future__ import annotations` and annotate all public APIs.
- **Docstrings** — public classes and methods require docstrings.
- **Changelog** — update `CHANGELOG.md` under `[Unreleased]`.

## Pull Request Process

1. Fork the repository and create a feature branch.
2. Commit your changes with clear messages.
3. Ensure `python -m pytest tests/ -v` passes locally.
4. Open a PR against `main` and fill in the PR template.
5. Address review comments promptly.

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.
