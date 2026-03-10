# Next Task: T-010 — Build Xcode approval observation harness

## Selected Task

- **ID:** T-010
- **Name:** Build Xcode approval observation harness
- **Priority:** P1
- **Dependencies:** none

## Description

Create a deterministic observation harness for Xcode MCP approval behavior. The harness should
run scripted MCP startup sequences against `xcrun mcpbridge` or `mcpbridge-wrapper`, record
timestamped protocol events, and make it easy to answer whether late catalog readiness is
surfaced via retries, EOF/reconnect, or `notifications/tools/list_changed` after the user clicks
Allow in Xcode.

## Outputs

- `SPECS/INPROGRESS/T-010_Build_Xcode_approval_observation_harness.md`
- `SPECS/INPROGRESS/T-010_Validation_Report.md`
- `scripts/xcode_approval_harness.py`
- `tests/unit/test_xcode_approval_harness.py`

## Recently Archived

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
