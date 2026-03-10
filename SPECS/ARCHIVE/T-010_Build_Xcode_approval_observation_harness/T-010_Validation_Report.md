# Validation Report: T-010 — Build Xcode approval observation harness

**Date:** 2026-03-10
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Harness can execute deterministic MCP handshake scenarios against `xcrun mcpbridge` or a wrapper command | ✅ PASS |
| 2 | Harness records timestamped send/receive events, EOF boundaries, and idle timeout windows | ✅ PASS |
| 3 | Harness can pause around named startup steps to create a stable manual Xcode approval window | ✅ PASS |
| 4 | Harness records whether `notifications/tools/list_changed` appears after approval | ✅ PASS |
| 5 | Unit coverage for scenario construction, parsing, summaries, and CLI behavior passes | ✅ PASS |
| 6 | Documentation points operators to the harness for approval-race investigation | ✅ PASS |

---

## Evidence

### Functional behavior

- Added `scripts/xcode_approval_harness.py`, a repo-local CLI harness that drives scripted
  MCP startup sequences against either the default `xcrun mcpbridge` target or an override
  command provided after `--`.
- The harness uses the same baseline MCP protocol version (`2024-11-05`) that the current
  broker path sends to Apple's bridge, so live probes stay aligned with the repo's existing
  transport behavior.
- Implemented two deterministic scenarios:
  - `approval-probe` for `initialize`, `notifications/initialized`, `tools/list`,
    `resources/list`, `resources/templates/list`, and `prompts/list`
  - `tools-only` for repeated `tools/list` probing after initialization
- The harness records:
  - outbound JSON-RPC steps with timestamps
  - inbound stdout JSON-RPC responses/notifications with parsed summaries
  - stderr text lines
  - idle timeout boundaries
  - stdout/stderr EOF markers
  - final process exit code
- Added summary extraction that reports response IDs, observed `tools/list` sizes,
  whether any non-empty tool catalog was seen, whether `notifications/tools/list_changed`
  appeared, and whether stdout hit EOF.

### Regression coverage

- `tests/unit/test_xcode_approval_harness.py`
  - verifies both scenario layouts
  - verifies unknown scenario rejection
  - verifies stable parsing/formatting of JSON-RPC and plain-text lines
  - verifies default command handling and `--` override behavior
  - verifies timeout validation
  - verifies summary extraction for late `notifications/tools/list_changed`

### Documentation updates

- `docs/troubleshooting.md`
  - added a new "Protocol observation harness" note to the Xcode approval race section
- `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`
  - added the matching DocC note
- `FEATURE_REBUILD/ObservedBehavior.md`
  - recorded the harness as supplemental observation tooling for approval-race analysis

### Live smoke observation

The harness was exercised against the published broker entrypoint:

```bash
python3 scripts/xcode_approval_harness.py \
  --pretty \
  --scenario tools-only \
  --step-delay 0.2 \
  --read-timeout 2.0 \
  --final-read-timeout 2.0 \
  --output logs/xcode-approval-harness-smoke.jsonl \
  -- \
  uvx --isolated --no-config --from mcpbridge-wrapper mcpbridge-wrapper --broker
```

This specific run was performed without a synchronized click on the Xcode **Allow** dialog,
so the captured timeline represents pre-approval startup behavior rather than post-approval
catalog recovery.

Observed result:

- no JSON-RPC response arrived within the configured 2-second read windows
- no `notifications/tools/list_changed` was observed
- the emitted JSONL and pretty timeline captured the startup stall precisely, which is the
  intended debugging value of the harness

Summary emitted by the harness:

```json
{
  "events_recorded": 13,
  "response_ids": [],
  "saw_non_empty_tools_list": false,
  "saw_stdout_eof": false,
  "saw_tools_list_changed": false,
  "timeout_count": 6,
  "tools_list_sizes": []
}
```

### Interactive synchronized approval run

The harness was then exercised directly against `xcrun mcpbridge` with a synchronized user
click on the Xcode **Allow** dialog during the scripted pause before `tools/list`:

```bash
python3 scripts/xcode_approval_harness.py \
  --pretty \
  --scenario approval-probe \
  --step-delay 0.2 \
  --pause-before-step tools-list \
  --pause-seconds 30 \
  --read-timeout 3.0 \
  --final-read-timeout 8.0 \
  --output logs/xcode-approval-direct.jsonl
```

Observed result:

- `initialize` returned immediately before the manual approval window
- after the synchronized **Allow** click, the first `tools/list` returned a full catalog of
  20 tools
- `resources/list`, `resources/templates/list`, and `prompts/list` all returned successfully
- no `notifications/tools/list_changed` was observed at any point in the run
- stdout remained open throughout the observation window; the harness terminated the child
  process itself at the end of the capture

Summary emitted by the harness:

```json
{
  "events_recorded": 21,
  "response_ids": [1, 2, 3, 4, 5],
  "saw_non_empty_tools_list": true,
  "saw_stdout_eof": false,
  "saw_tools_list_changed": false,
  "timeout_count": 7,
  "tools_list_sizes": [20]
}
```

---

## Quality Gate Results

| Gate | Result |
|------|--------|
| `pytest tests/unit/test_xcode_approval_harness.py -v` | 10 passed |
| `python3 scripts/xcode_approval_harness.py --help` | PASS |
| `ruff check scripts/xcode_approval_harness.py tests/unit/test_xcode_approval_harness.py` | All checks passed |
| `ruff check src/` | All checks passed |
| `mypy src/` | Success: no issues found in 20 source files |
| `pytest --cov` | 912 passed, 5 skipped, 2 warnings; coverage 91.55% |
| `python3 scripts/check_doc_sync.py --all` | DocC sync checks passed |

---

## Changed Files

- `scripts/xcode_approval_harness.py`
- `tests/unit/test_xcode_approval_harness.py`
- `docs/troubleshooting.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`
- `FEATURE_REBUILD/ObservedBehavior.md`
