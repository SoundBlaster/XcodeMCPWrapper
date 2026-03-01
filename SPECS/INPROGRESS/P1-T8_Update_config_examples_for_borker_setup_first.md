# PRD: P1-T8 — Update /config examples for borker setup first

## Overview

`README.md` already presents broker setup first, but several standalone templates in
`config/` still lead with non-broker examples. This task aligns those templates
with current guidance by presenting broker-mode setup first for supported MCP
clients.

## Problem Statement

Users often copy from `config/` files directly. When non-broker examples appear
first, the docs and templates send mixed signals about the preferred setup path.
With `--broker` now the primary mode, templates should reflect that ordering.

## Scope

In scope:
- Reorder options in `config/cursor-mcp.json` and `config/zed-agent.json` so a
  broker-mode configuration is listed first.
- Update `config/claude-code.txt` and `config/codex-cli.txt` so broker setup
  commands are shown before non-broker alternatives.
- Keep command syntax compatible with current `--broker` guidance.

Out of scope:
- Runtime behavior changes in Python source code.
- Changes to broker-specific template files that already lead with broker mode.

## Deliverables

| File(s) | Change |
|---|---|
| `config/cursor-mcp.json` | Broker option block moved to first position and labeled as recommended |
| `config/zed-agent.json` | Broker option block moved to first position and labeled as recommended |
| `config/claude-code.txt` | Broker command block added as first option |
| `config/codex-cli.txt` | Broker command block added as first option |

## Acceptance Criteria

- [ ] `config/cursor-mcp.json` presents a broker-mode option first in `xcode-tools` options.
- [ ] `config/zed-agent.json` presents a broker-mode option first in `xcode-tools` options.
- [ ] `config/claude-code.txt` lists a broker setup command before non-broker options.
- [ ] `config/codex-cli.txt` lists a broker setup command before non-broker options.
- [ ] Full quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (>= 90%).

## Validation Plan

1. Inspect option ordering in each updated config template.
2. Run `pytest`.
3. Run `ruff check src/`.
4. Run `mypy src/`.
5. Run `pytest --cov` and confirm coverage remains >= 90%.

## Dependencies

- P2-T6

## Risks

Low. This is a documentation/template ordering change and does not alter runtime
logic.
