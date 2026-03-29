# Validation Report: P1-T14

## Task

Document Codex Desktop resource-probe behavior for Xcode tools MCP connectivity

## Date

2026-03-29

## Changes Made

### Markdown docs

- `README.md`
  - Added explicit Known Issues note for Codex Desktop `resources/list` /
    `resources/templates/list` probes and clarified that `-32601` on those
    probes is non-fatal when tool calls succeed.
- `docs/troubleshooting.md`
  - Added troubleshooting section for unknown resource-method errors and
    guidance to verify via Xcode tool calls (`XcodeListWindows`, `XcodeLS`).
- `docs/codex-setup.md`
  - Added Codex Desktop note and troubleshooting entry clarifying expected
    resource-probe behavior.

### DocC mirrors

- `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/CodexCLISetup.md`

Mirrors were updated to match the corresponding Markdown guidance.

## Quality Gate Results

| Gate | Result |
|------|--------|
| `pytest` | PASS (`923 passed, 5 skipped`) |
| `ruff check src/` | PASS (`All checks passed`) |
| `mypy src/` | PASS (`Success: no issues found in 20 source files`) |
| `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` | PASS (`91.62%`, threshold `>= 90%`) |
| `python scripts/check_doc_sync.py` (unstaged scope) | PASS |
| `make doccheck-all` | PARTIAL — branch-scope warning while README/codex Markdown commits and matching DocC updates are not yet in the same commit history snapshot |

## Verdict

PASS
