# Next Task: None

## Selected Task

- No active task selected.

## Description

All tasks currently tracked in `SPECS/Workplan.md` are archived or completed. Select a new
task only after a follow-up or new workplan entry is created.

## Outputs

- None.

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
