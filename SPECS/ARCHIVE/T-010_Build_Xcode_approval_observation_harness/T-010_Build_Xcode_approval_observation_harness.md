# PRD: T-010 — Build Xcode approval observation harness

**Task ID:** T-010
**Priority:** P1
**Status:** Planned
**Date:** 2026-03-10
**Owner:** Codex

## Problem Statement

We need a deterministic way to observe how `xcrun mcpbridge` and `mcpbridge-wrapper`
behave around the Xcode GUI approval flow. Manual probing has shown multiple race-shaped
outcomes across Cursor and Zed, but the repo lacks a repeatable harness that can capture
the exact order and timing of MCP messages before and after the user clicks **Allow** in
Xcode.

## Goals

1. Provide a repo-local CLI harness that can run scripted MCP startup scenarios.
2. Capture timestamped protocol events, timeout windows, and EOF boundaries in a format
   suitable for post-run analysis.
3. Make it easy to answer whether readiness appears via:
   - normal `initialize` + `tools/list` responses,
   - reconnect / EOF patterns,
   - or late `notifications/tools/list_changed`.

## Non-Goals

1. Automate the Xcode GUI approval click itself.
2. Change broker/runtime behavior in production code.
3. Add a packaged user-facing command to the published PyPI distribution.

## Deliverables

1. `scripts/xcode_approval_harness.py`
   - CLI entrypoint for deterministic MCP observation runs.
2. `tests/unit/test_xcode_approval_harness.py`
   - Unit coverage for scenario parsing, event formatting, and timeout handling.
3. `docs/troubleshooting.md`
   - Short operator note pointing to the harness for approval-race diagnostics.
4. `FEATURE_REBUILD/ObservedBehavior.md`
   - Document the harness as a repeatable observation tool for external Xcode behavior.
5. `SPECS/INPROGRESS/T-010_Validation_Report.md`
   - Captured quality-gate results and a brief manual smoke-run note.

## Functional Requirements

1. The harness MUST support launching either:
   - `xcrun mcpbridge`, or
   - an arbitrary command supplied after `--`.
2. The harness MUST send newline-delimited JSON-RPC messages in a deterministic sequence.
3. The harness MUST support per-step delays so runs can pause around manual Xcode approval.
4. The harness MUST timestamp every sent and received event relative to process start.
5. The harness MUST record:
   - outgoing request/notification payloads,
   - incoming responses/notifications,
   - EOF,
   - timeout markers,
   - process exit code.
6. The harness MUST highlight whether `notifications/tools/list_changed` was observed.
7. The harness MUST be usable without modifying installed package metadata or editor config.

## CLI Design

Planned flags:

- `--scenario <name>`: named scenario preset.
- `--step-delay <seconds>`: default delay between scripted steps.
- `--read-timeout <seconds>`: timeout for waiting on incoming lines.
- `--output <path>`: optional JSONL event log file.
- `--pretty`: also print human-readable event summary to stdout.
- `--`: optional command override; defaults to `xcrun mcpbridge`.

Planned scenario presets:

1. `approval-probe`
   - `initialize`
   - `notifications/initialized`
   - `tools/list`
   - `resources/list`
   - `prompts/list`
2. `tools-only`
   - `initialize`
   - `notifications/initialized`
   - repeated `tools/list`

## Output Contract

Each event line SHOULD be JSON with at least:

```json
{
  "t_ms": 1234,
  "direction": "send|recv|meta",
  "event": "jsonrpc|timeout|eof|exit",
  "summary": "tools/list",
  "payload": {}
}
```

The harness SHOULD print a final summary including:

- observed response IDs
- whether a non-empty `tools/list` was seen
- whether `notifications/tools/list_changed` was seen
- whether EOF occurred before readiness

## Test Plan

Automated:

1. Parse scenario presets into the expected ordered message list.
2. Format JSONL event records deterministically.
3. Recognize `tools/list_changed`, `tools/list`, EOF, and timeout markers.
4. Validate `--help` and CLI argument parsing.

Manual smoke:

1. Run harness against the live `xcrun mcpbridge`.
2. Pause for Xcode approval.
3. Confirm event log is written and summary renders.

## Verification Commands

```bash
pytest tests/unit/test_xcode_approval_harness.py -v
python3 scripts/xcode_approval_harness.py --help
ruff check src/ tests/ scripts/
mypy src/
pytest --cov
```

## Risks

1. Real Xcode approval timing is inherently nondeterministic; the harness can observe it
   but cannot stabilize it.
2. Live smoke runs depend on a local Xcode session and cannot be asserted in CI.
3. `xcrun mcpbridge` may emit no explicit approval event, leaving the harness to infer
   readiness from message timing and catalog contents.
