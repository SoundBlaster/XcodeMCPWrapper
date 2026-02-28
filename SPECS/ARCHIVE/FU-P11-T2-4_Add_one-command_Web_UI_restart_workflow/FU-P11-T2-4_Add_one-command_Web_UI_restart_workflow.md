# PRD: FU-P11-T2-4 — Add one-command Web UI restart workflow

## Objective

Provide a single, reliable restart command for the Web UI server that works in local development and packaged/uvx usage. The restart flow must reclaim the selected port even when a stale listener exists, preferring graceful shutdown and using force-kill only when necessary.

## Deliverables

- CLI restart support in `src/mcpbridge_wrapper/__main__.py` (or delegated helper) that:
  - Detects listeners on the target Web UI port
  - Attempts graceful termination first
  - Falls back to forceful termination when required
  - Starts a fresh Web UI process using the existing startup path
- `Makefile` target `webui-restart` for one-command local restart
- Troubleshooting docs updates in:
  - `docs/troubleshooting.md`
  - `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`
- Automated tests for restart behavior and occupied-port edge cases

## Acceptance Criteria

- One documented command restarts Web UI on a chosen port without manual PID lookup.
- Restart flow performs graceful stop first and force-kills only if needed.
- Workflow works for both local/dev install and uvx usage.
- Tests cover restart behavior and practical port-occupied edge cases.

## Dependencies and Constraints

- Depends on `P11-T2` Web UI infrastructure.
- Keep compatibility with current CLI flags and startup flow.
- Avoid introducing platform-only behavior beyond existing macOS assumptions in this repo.

## Test-First Plan

1. Add/extend unit tests for restart helpers:
   - Process lookup by port
   - Graceful->forceful termination sequence
   - No-op when no listener exists
2. Add CLI-level tests for restart command wiring.
3. Implement minimal code to satisfy tests.
4. Add/adjust docs and ensure examples are executable.

## Implementation Phases

### Phase 1: Restart primitives
- Inputs: target port, timeout, startup arguments
- Outputs: deterministic restart routine with logging/messages
- Verification: unit tests for success/fallback/failure handling

### Phase 2: CLI and Makefile integration
- Inputs: CLI argument parsing and existing web-ui commands
- Outputs: command/flag to restart + `make webui-restart`
- Verification: CLI tests and manual command dry-check

### Phase 3: Documentation and validation
- Inputs: final command syntax and expected behavior
- Outputs: troubleshooting docs updated in both markdown/docc
- Verification: command examples align across docs

## Validation Commands

- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

## Notes

- Keep restart idempotent so repeated calls do not fail when no process is running.
- Reuse existing process management helpers if present instead of duplicating logic.

---
**Archived:** 2026-02-28
**Verdict:** PASS
