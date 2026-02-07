# PRD: P1-T2 - Initialize Python Project with pyproject.toml

## Task Information

- **Task ID:** P1-T2
- **Task Name:** Initialize Python project with pyproject.toml
- **Phase:** Phase 1 (Foundation & Scaffolding)
- **Priority:** P0

## Overview

Create a `pyproject.toml` file with project metadata, build system configuration, Python 3.7+ requirement, and executable entry point for the mcpbridge-wrapper package.

## Deliverables

1. `pyproject.toml` - Project configuration file with:
   - [project] section with metadata (name, version, description, authors, etc.)
   - [build-system] section with setuptools/wheel
   - [project.scripts] section for CLI entry point
   - Python 3.7+ requirement

## Acceptance Criteria

- [ ] `pyproject.toml` exists at project root
- [ ] `pip install -e .` succeeds without errors
- [ ] Package is importable after installation
- [ ] `mcpbridge-wrapper` command is available after installation (entry point configured)

## Dependencies

- P1-T1 [✓ DONE] - Project directory structure

## Implementation Notes

- Use modern pyproject.toml format (PEP 621)
- Configure setuptools as build backend
- Set Python version requirement to >=3.7
- Define console script entry point for the wrapper

## Validation Steps

1. Verify pyproject.toml exists: `ls -la pyproject.toml`
2. Verify editable install works: `pip install -e .`
3. Verify package import: `python3 -c "import mcpbridge_wrapper"`
4. Verify entry point: `which mcpbridge-wrapper` or `mcpbridge-wrapper --help`

## Sign-off

- [ ] pyproject.toml created with all required sections
- [ ] Acceptance criteria met
- [ ] Validation passed
