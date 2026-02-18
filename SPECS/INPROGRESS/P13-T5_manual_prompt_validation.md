# Manual Prompt Validation: P13-T5

**Date:** 2026-02-18
**Task:** Validate reduced Xcode permission prompt behavior in broker mode

## Environment checks

- `xcrun mcpbridge --help` executed successfully.
- Xcode process detected (`pgrep -x Xcode` returned a running PID during validation).

## Manual procedure

1. Start from a clean state (no stale broker processes/sockets).
2. Run repeated short-lived sessions in direct mode and record prompt behavior.
3. Run repeated short-lived sessions in broker mode and record prompt behavior.
4. Confirm whether prompts reappear while the broker-owned upstream session remains running.

## Result

**Status:** ⚠️ PARTIAL

- Automated evidence confirms broker mode keeps a single upstream process across many short-lived sessions.
- Interactive macOS prompt observation could not be fully captured from this non-interactive terminal workflow.
- A human-operated verification pass in an interactive desktop session is still required to conclusively mark prompt behavior as PASS.

## Supporting automated evidence

- `tests/integration/test_broker_multi_client.py` covers sequential reuse and concurrent stability.
- `test_broker_mode_launches_upstream_once_for_many_short_lived_clients` verifies a single upstream launch across 12 short-lived sessions.
- `SPECS/INPROGRESS/P13-T5_process_churn_metrics.md` captures direct-vs-broker churn comparison.
