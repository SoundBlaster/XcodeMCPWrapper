# Contributing to mcpbridge-wrapper

Thank you for your interest in contributing! This document outlines the development workflow and quality gates.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Quality Gates

All code must pass the following quality gates before being merged:

### 1. Tests (pytest)

Run all tests with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term
```

Requirements:
- All tests must pass
- Coverage must remain ≥90%

### 2. Linting (ruff)

Check for code issues:

```bash
ruff check src/ tests/
```

Auto-fix issues where possible:

```bash
ruff check src/ tests/ --fix
```

### 3. Formatting (ruff)

Check code formatting:

```bash
ruff format --check src/ tests/
```

Apply formatting:

```bash
ruff format src/ tests/
```

### 4. Type Checking (mypy)

```bash
mypy src/
```

### 5. Doc Sync Check

Ensure documentation changes are synced with DocC catalog:

```bash
make doccheck
# or
python scripts/check_doc_sync.py
```

This checks that changes to `docs/*.md` files are also reflected in the DocC catalog (`mcpbridge-wrapper.docc/`).

### 6. Build Verification

Ensure the package builds correctly:

```bash
python -m build
twine check dist/*
```

## Quick Check Script

Run all quality gates at once:

```bash
make test && make lint && make typecheck
```

Or use this bash script (save as `check.sh`):

```bash
#!/bin/bash
set -e

echo "=== Running Quality Gates ==="

echo "1. Running tests..."
pytest tests/ -v --cov=src --cov-report=term

echo "2. Running linter..."
ruff check src/ tests/

echo "3. Checking format..."
ruff format --check src/ tests/

echo "4. Running type checker..."
mypy src/

echo "5. Checking doc sync..."
python scripts/check_doc_sync.py

echo "6. Building package..."
python -m build && twine check dist/*

echo "=== All Quality Gates Passed ==="
```

Make it executable and run:

```bash
chmod +x check.sh
./check.sh
```

## Workflow

We follow the [FLOW.md](SPECS/COMMANDS/FLOW.md) workflow:

1. **BRANCH** - Create a feature branch from `main`
2. **SELECT** - Pick a task from the workplan
3. **PLAN** - Create a PRD for the task
4. **EXECUTE** - Implement and run quality gates
5. **ARCHIVE** - Move completed task to archive

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/TASK-ID-description`
2. Make your changes and run quality gates
3. Commit with clear messages
4. Push to your fork
5. Create a Pull Request against `main`

## CI/CD

All PRs trigger GitHub Actions CI which runs:
- Lint & Type Check (Python 3.11)
- Tests (Python 3.9, 3.10, 3.11, 3.12)
- Package Build

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for details.

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for public functions
- Keep functions focused and small

## Questions?

Open an issue or check the [troubleshooting guide](docs/troubleshooting.md).
