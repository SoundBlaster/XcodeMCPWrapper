# PRD: P1-T5 - Create Makefile with Common Tasks

## Task Information

- **Task ID:** P1-T5
- **Task Name:** Create Makefile with Common Tasks
- **Phase:** Phase 1 (Foundation & Scaffolding)
- **Priority:** P1

## Overview

Create a Makefile with common development tasks for the mcpbridge-wrapper project.

## Deliverables

1. `Makefile` at project root with targets:
   - `test` - Run pytest
   - `lint` - Run ruff check
   - `format` - Run ruff format
   - `typecheck` - Run mypy
   - `install` - Install package in editable mode
   - `clean` - Clean build artifacts

## Acceptance Criteria

- [ ] `make test` runs pytest
- [ ] `make lint` runs ruff check
- [ ] All Makefile targets work without errors

## Dependencies

- P1-T3 [✓ DONE] - ruff configured
- P1-T4 [✓ DONE] - pytest configured

## Implementation Notes

- Use standard Makefile syntax
- Add .PHONY for all targets
- Include help target for documentation

## Validation Steps

1. Verify Makefile exists: `ls -la Makefile`
2. Verify test target: `make test`
3. Verify lint target: `make lint`

## Sign-off

- [ ] Makefile created with all targets
- [ ] Acceptance criteria met
