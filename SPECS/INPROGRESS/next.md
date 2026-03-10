# Next Task: T-011 — Emit synthetic broker tools/list_changed on catalog warm-up

## Selected Task

- **ID:** T-011
- **Name:** Emit synthetic broker tools/list_changed on catalog warm-up
- **Priority:** P1
- **Dependencies:** T-010

## Description

Extend the broker so clients receive a `notifications/tools/list_changed` hint when the Xcode
tool catalog becomes available after approval, even if upstream `xcrun mcpbridge` does not emit
that notification itself. Reuse the existing internal warm-up probes rather than adding a second
slow watcher loop.

## Outputs

- `SPECS/INPROGRESS/T-011_Emit_synthetic_broker_tools_list_changed_on_catalog_warm-up.md`
- `SPECS/INPROGRESS/T-011_Validation_Report.md`
- `src/mcpbridge_wrapper/broker/daemon.py`
- `src/mcpbridge_wrapper/broker/transport.py`
- `tests/unit/test_broker_daemon.py`
- `tests/unit/test_broker_transport.py`

## Recently Archived

- `2026-03-10` — `T-010` archived with verdict `PASS`
- `2026-03-10` — `P8-T2` archived with verdict `PASS`
- `2026-03-10` — `P1-T13` archived with verdict `PASS`
- `2026-03-10` — `P2-T8` archived with verdict `PASS`
- `2026-03-07` — `P8-T1` archived with verdict `PASS`
- `2026-03-07` — `P7-T5` archived with verdict `PASS`
- `2026-03-07` — `P7-T4` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T3-2` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T3-1` archived with verdict `PASS`

## Post-Merge Action Required

After the `P8-T2` PR merges to `main`, push the release tag to trigger publishing:

```bash
git checkout main && git pull origin main
git tag v0.4.3
git push origin v0.4.3
```

Then verify GitHub Actions `publish-mcp.yml` completes successfully.
