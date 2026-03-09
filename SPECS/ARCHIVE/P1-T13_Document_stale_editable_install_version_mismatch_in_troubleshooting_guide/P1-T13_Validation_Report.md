# Validation Report: P1-T13

## Task

Document stale editable install version mismatch in troubleshooting guide

## Date

2026-03-10

## Changes Made

### `docs/troubleshooting.md`

Added new entry `### "Package Version" shows old release after version bump (development environment)` before the "Debug Mode" section. The entry covers:

- Symptom: `--doctor` version mismatch with old package version from `.venv` dist-info
- Root cause: editable install dist-info is written at `pip install -e .` time, not at `pyproject.toml` bump time
- Clarification: `uvx` fetches from PyPI independently of `.venv`
- Fix: `.venv/bin/pip install -e .` to refresh dist-info

### `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`

Added matching section `## "Package Version" shows old release after version bump (development environment)` before the "Debug Mode" section. Content is condensed to DocC style (no client-specific sub-steps needed since this is a dev-only scenario).

## Quality Gate Results

| Gate | Result |
|------|--------|
| `pytest` | 902 passed, 5 skipped |
| `ruff check src/` | All checks passed |
| `mypy src/` | Success: no issues found in 20 source files |
| `pytest --cov` | 91.55% (≥ 90% required) ✅ |
| `make doccheck-all` | ✓ DocC documentation is in sync ✅ |

## Verdict

PASS
