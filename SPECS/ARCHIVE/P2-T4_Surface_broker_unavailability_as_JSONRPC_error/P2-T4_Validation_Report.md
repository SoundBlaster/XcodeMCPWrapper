# Validation Report: P2-T4 — Surface broker unavailability as JSON-RPC error

**Date:** 2026-03-01
**Status:** PASS

## Changes Delivered

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/proxy.py` | Added `import json`; added `_send_broker_error()` helper; wrapped connect phase in `run()` with try/except |
| `tests/unit/test_broker_proxy.py` | Updated `test_returns_with_error_when_no_socket`; added `TestBrokerProxyUnavailableError` (5 tests) |
| `tests/unit/test_broker_stubs.py` | Updated `test_run_raises_timeout_when_no_socket` → `test_run_writes_error_when_no_socket` to match new behaviour |

## Acceptance Criteria

- [x] Connection timeout produces a JSON-RPC `-32001` error response written to stdout
- [x] Error message includes a human-readable reason (`"Broker unavailable: <reason>"`)
- [x] `run()` returns without re-raising — client does not hang indefinitely
- [x] All existing broker tests pass (updated 2 tests whose behaviour legitimately changed)
- [x] `pytest --cov` coverage ≥ 90% (achieved 91.59%)
- [x] `ruff check src/` passes
- [x] `ruff format --check src/ tests/` passes

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest -q` | 732 passed, 5 skipped |
| `pytest --cov` coverage | 91.59% (≥ 90% required) |
| `ruff check src/` | PASS |
| `ruff format --check src/ tests/` | PASS |

## Implementation Notes

- `_send_broker_error(reason)` constructs a JSON-RPC 2.0 error with code `-32001` and
  message `"Broker unavailable: {reason}"`, using `id: null` (permitted by JSON-RPC 2.0 §5
  when the request id cannot be determined).
- The connect phase in `run()` is wrapped with `except Exception` to catch `TimeoutError`,
  `ConnectionRefusedError`, `FileNotFoundError`, and any `OSError` subclass from spawn.
- `_send_broker_error` guards against `_make_stdout_writer()` failing in non-pipe contexts
  (e.g., test environments) with an inner try/except that logs and returns.
- Two existing tests (`test_raises_timeout_when_no_socket` in both proxy and stubs test files)
  were updated: they previously expected `run()` to raise `TimeoutError`; the new behaviour is
  that `run()` returns cleanly after writing the JSON-RPC error. Both tests now verify the
  error payload instead.
