# Next Task: Unselected

## Selected Task

No active task is selected in `SPECS/INPROGRESS/`.

The most recently completed task was `T-011 — Emit synthetic broker tools/list_changed on catalog warm-up`,
archived on `2026-03-10` with verdict `PASS`.

## Recently Archived

- `2026-03-10` — `T-011` archived with verdict `PASS`
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
