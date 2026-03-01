# PRD: P2-T6 — Remove legacy --broker-connect and --broker-spawn flags

## Overview

`--broker` is already the single recommended proxy-mode flag. The legacy aliases
`--broker-connect` and `--broker-spawn` were retained only for backwards
compatibility, but broker mode has not been released. This task removes the
legacy aliases from CLI behavior, tests, and documentation to reduce user-facing
complexity.

## Problem Statement

Current state keeps three proxy entry flags (`--broker`, `--broker-connect`,
`--broker-spawn`) and carries alias-specific docs/tests. This increases support
surface and can confuse users about which mode to configure.

## Scope

In scope:
- Remove legacy alias parsing in CLI broker argument handling.
- Keep `--broker` (proxy auto-detect/spawn) and `--broker-daemon` (host mode).
- Remove alias-focused tests and update expectations to the two-flag model.
- Remove legacy alias guidance/examples from user docs.

Out of scope:
- Behavioral changes to broker daemon/proxy internals unrelated to flag parsing.
- New broker features.

## Deliverables

| File(s) | Change |
|---|---|
| `src/mcpbridge_wrapper/__main__.py` | Remove `--broker-connect` / `--broker-spawn` broker-control parsing and related wording |
| `tests/unit/test_main.py` | Remove/update alias tests and comments for parser/main flows |
| `tests/unit/test_broker_proxy.py` | Update legacy-flag references in test descriptions to current flags |
| `README.md`, `docs/*.md` | Remove alias guidance/examples; keep `--broker` + `--broker-daemon` guidance only |

## Acceptance Criteria

- [ ] Wrapper no longer accepts `--broker-connect` and `--broker-spawn` as broker control flags.
- [ ] Broker-mode docs no longer present aliases as usable/recommended options.
- [ ] Broker guidance remains clear for `--broker` (proxy) and `--broker-daemon` (host).
- [ ] Quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (coverage >= 90%).

## Validation Plan

1. Run parser/unit tests and full test suite.
2. Run lint and type checks.
3. Run coverage and confirm >= 90%.
4. Verify no remaining legacy-flag references in active docs/code paths.

## Dependencies

- P2-T1

## Risks

Low-medium: removing aliases is a CLI behavior change. Mitigate by fully
aligning docs/tests and preserving clear `--broker`/`--broker-daemon`
instructions.

---
**Archived:** 2026-03-01
**Verdict:** PASS
