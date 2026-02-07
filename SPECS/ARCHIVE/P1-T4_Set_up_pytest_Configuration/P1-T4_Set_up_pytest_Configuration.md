# PRD: P1-T4 - Set up pytest Configuration

## Task Information

- **Task ID:** P1-T4
- **Task Name:** Set up pytest Configuration
- **Phase:** Phase 1 (Foundation & Scaffolding)
- **Priority:** P0

## Overview

Configure pytest with coverage reporting in pyproject.toml to enable test discovery, execution, and coverage reporting.

## Deliverables

1. `[tool.pytest.ini_options]` section in pyproject.toml with:
   - testpaths pointing to tests/
   - python_files pattern for test discovery
   - addopts for default pytest options
2. `[tool.coverage.run]` section in pyproject.toml with:
   - source directory configuration
   - omit patterns for non-source files

## Acceptance Criteria

- [ ] `pytest --version` reads config without errors
- [ ] `pytest` runs successfully (even with 0 tests in new directories)
- [ ] Coverage configuration is recognized by pytest-cov

## Dependencies

- P1-T2 [✓ DONE] - pyproject.toml exists

## Implementation Notes

- Add pytest configuration to existing pyproject.toml
- Configure testpaths to include both tests/unit and tests/integration
- Set up coverage to track src/mcpbridge_wrapper/
- Target coverage threshold: 90%

## Validation Steps

1. Verify pytest reads config: `pytest --version`
2. Verify pytest runs: `pytest tests/ -v`
3. Verify coverage works: `pytest --cov=src`

## Sign-off

- [ ] pytest configuration added to pyproject.toml
- [ ] Coverage configuration added to pyproject.toml
- [ ] Acceptance criteria met
