# P6-T10: Create GitHub CI Workflow

## Overview

Create a comprehensive GitHub Actions workflow for continuous integration that validates the project state on every push and pull request.

## Context

The project currently has:
- Python package with pyproject.toml
- pytest with coverage configuration
- ruff for linting and formatting
- mypy for type checking
- Existing docs.yml and publish-mcp.yml workflows

We need a CI workflow to ensure code quality is maintained automatically.

## Deliverables

1. `.github/workflows/ci.yml` - Main CI workflow file

## Acceptance Criteria

- Workflow triggers on push to main and pull requests to main
- Workflow can be triggered manually via workflow_dispatch
- Multiple jobs run in parallel:
  - lint: ruff check, ruff format --check, mypy
  - test: pytest with coverage on Python 3.9, 3.10, 3.11, 3.12
  - build: build package and validate with twine
- All jobs must pass for CI to be green
- Build artifacts are uploaded for inspection

## Design

### Workflow Structure

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Set up Python 3.11
      - Install ruff, mypy
      - Run ruff check
      - Run ruff format --check
      - Run mypy

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - Checkout code
      - Set up Python ${{ matrix.python-version }}
      - Install dependencies
      - Run pytest with coverage

  build:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Set up Python 3.11
      - Install build, twine
      - Build package
      - Check with twine
      - Upload artifacts
```

## Implementation Steps

1. Create `.github/workflows/ci.yml`
2. Test workflow syntax
3. Verify all quality gates are covered

## Dependencies

- P1-T2: Python Project with pyproject.toml
- P1-T3: Linting and Formatting Tools
- P1-T4: pytest Configuration
