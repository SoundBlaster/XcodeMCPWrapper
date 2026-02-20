# PLAN: BUG-T15 — Web UI Port + Config MCP Startup Failure

## Objective
Determine why MCP runs with both `--web-ui-port` and `--web-ui-config` can produce an unreachable dashboard, then ship a fix that is observable in logs, documented, and covered by tests. The core outcome is deterministic startup behavior with explicit precedence and actionable diagnostics.

## Scope
- In scope:
  - Reproduce startup path for `--web-ui --web-ui-port 8080 --web-ui-config <file>`.
  - Confirm actual failure mode(s): port collision, bind host mismatch, or startup skip behavior.
  - Adjust runtime behavior and/or diagnostics in `src/mcpbridge_wrapper/__main__.py`.
  - Align docs examples and precedence explanation.
  - Add regression tests for precedence + failure messaging.
- Out of scope:
  - Redesigning Web UI lifecycle architecture.
  - Persistent broker work (Phase 13).

## Acceptance Criteria
- MCP launch with both flags has predictable, documented precedence behavior.
- Failure mode is surfaced clearly in stderr and troubleshooting docs.
- Docs avoid ambiguous examples likely to break in multi-process client runs.
- New/updated tests fail before fix and pass after fix.

## Test-First Plan
1. Add/adjust unit tests for web-ui arg precedence and startup diagnostics.
2. Add regression test covering combined flags scenario and expected final port source.
3. Run full quality gates: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (>=90%).

## Execution Plan
1. Reproduction and Evidence
- Inputs: current CLI parsing/startup code, docs examples.
- Outputs: confirmed root cause with exact log path.
- Verification: reproduce behavior locally via test or controlled command.

2. Runtime Fix
- Inputs: `__main__.py` web-ui init flow.
- Outputs: deterministic precedence and improved warning/error text.
- Verification: unit tests for selected behavior and message text.

3. Documentation and Validation
- Inputs: `docs/webui-setup.md`, optionally troubleshooting references.
- Outputs: corrected MCP config guidance.
- Verification: docs contain consistent examples; validation report records outcomes.

## Notes
- Keep backward compatibility where possible; prefer clarity over silent fallback.
- If behavior remains override-by-CLI, docs must state that explicitly and warn about collisions.
