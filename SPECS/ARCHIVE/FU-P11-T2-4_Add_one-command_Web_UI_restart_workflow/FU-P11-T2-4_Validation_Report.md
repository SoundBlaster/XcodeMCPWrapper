# Validation Report: FU-P11-T2-4 — Add one-command Web UI restart workflow

**Date:** 2026-02-28
**Task ID:** FU-P11-T2-4
**Verdict:** PASS

## Scope Implemented

- Added `--web-ui-restart` CLI flag parsing.
- Implemented restart helpers to reclaim occupied Web UI ports:
  - listener PID discovery via `lsof`
  - graceful shutdown (`SIGTERM`) first
  - force kill (`SIGKILL`) fallback when needed
- Wired restart behavior into Web UI startup flow in `main()`.
- Added `Makefile` target `webui-restart` with configurable `PORT`.
- Updated troubleshooting docs (markdown + DocC) with one-command restart workflow for local and uvx usage.
- Added/updated unit tests for parser changes, restart helpers, and main restart wiring.

## Quality Gates

- `PYTHONPATH=src pytest` → PASS (`668 passed, 5 skipped`)
- `PYTHONPATH=src ruff check src/` → PASS
- `PYTHONPATH=src mypy src/` → PASS
- `PYTHONPATH=src pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` → PASS
  - Total coverage: **90.89%** (required: >= 90%)

## Acceptance Criteria Check

- [x] A single documented command restarts Web UI on a chosen port without manual PID hunting.
- [x] Restart flow attempts graceful stop first, then force-kill only if needed.
- [x] Works for both local/dev install and uvx usage.
- [x] Tests cover restart behavior and port-occupied edge case(s).

## Notes

- Port listener discovery relies on `lsof` availability (standard on macOS).
- Existing non-restart Web UI startup behavior is preserved.
