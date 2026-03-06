# P5-T1 PRD — Release 0.4.0 to PyPI and MCP Registry

## Task Metadata

- **Task ID:** P5-T1
- **Phase:** Phase 5: Release
- **Priority:** P0
- **Dependencies:** P1-T1, P1-T11, P2-T1 through P2-T6, P3-T11, P4-T1, P4-T2, BUG-T8
- **Source:** `SPECS/Workplan.md` open task entry

## Objective Summary

Prepare `v0.4.0` for publication by bringing all release-gate documents into alignment with the actual release date (2026-03-06) and verifying all automated quality gates pass on the current `main` HEAD. The CI/CD pipeline (`publish-mcp.yml`) is already wired for tag-triggered PyPI and MCP Registry publishing — no manual upload scripting is required. The task deliverable is a merge-ready branch that is confirmed to pass all gates, with the CHANGELOG date corrected and the manual release commands documented for the human operator to execute after PR merge.

**Scope boundary:** The `git tag v0.4.0` push and PyPI/MCP Registry publish are intentionally **out of scope** for this PR — they require PyPI credentials and human confirmation after merge. The PR description documents the exact commands required.

## Success Criteria

1. `CHANGELOG.md` line `## [0.4.0] - 2026-02-20` is changed to `## [0.4.0] - 2026-03-06`.
2. CI/CD workflow (`publish-mcp.yml`) reviewed and confirmed tag-triggered publish-ready.
3. All local quality gates pass: `make test` (≥ 90% coverage), `make lint`, `make format-check`, `make typecheck`, `make doccheck-all`, `make package-assets-check`.
4. `SPECS/Workplan.md` P5-T1 entry marked `✅ Completed (2026-03-06)`.
5. `SPECS/INPROGRESS/next.md` updated to reflect P5-T1 as most recently archived.
6. PR description includes exact tag + publish commands for human operator.

## Acceptance Tests

| Check | Tool / Command | Expected Result |
|-------|---------------|-----------------|
| CHANGELOG date | `grep "\[0\.4\.0\]" CHANGELOG.md` | `## [0.4.0] - 2026-03-06` |
| pytest + coverage | `make test` | ≥ 785 tests pass, coverage ≥ 90% |
| ruff lint | `make lint` | 0 errors |
| ruff format | `make format-check` | 0 errors |
| mypy | `make typecheck` | 0 errors |
| DocC sync | `make doccheck-all` | 0 drift |
| Package assets | `make package-assets-check` | Web UI assets present |
| Version in pyproject.toml | `grep ^version pyproject.toml` | `version = "0.4.0"` |
| server.json version | `jq .version server.json` | `"0.4.0"` |

## Test-First Plan

No code logic changes are required for this task. All quality gate runs are validation-only:

1. Run `make test` — confirm test count and coverage.
2. Run `make lint && make format-check && make typecheck` — confirm zero lint/type errors.
3. Run `make doccheck-all` — confirm DocC mirrors in sync.
4. Run `make package-assets-check` — confirm Web UI assets packaged.
5. Update CHANGELOG date (single line change).
6. Re-run `make test` to confirm nothing broken by the trivial text change.
7. Update Workplan and next.md.

## Implementation Plan (Hierarchical TODO)

### Phase A — Release Artifact Verification

- **Inputs:** Current `main` HEAD at `2deb0a0`.
- **Actions:**
  - Verify `pyproject.toml` version = `"0.4.0"`.
  - Verify `server.json` version = `"0.4.0"` and `packages[0].version = "0.4.0"`.
  - Review `publish-mcp.yml` and confirm it will trigger on `v*` tag push.
- **Outputs:** Confirmation notes for validation report.
- **Verification:** `grep`, `jq`, visual review of workflow triggers.

### Phase B — CHANGELOG Date Update

- **Inputs:** `CHANGELOG.md` line 8 reads `## [0.4.0] - 2026-02-20`.
- **Actions:**
  - Replace `2026-02-20` with `2026-03-06` in the `[0.4.0]` header line.
  - No other changelog lines require modification.
- **Outputs:** `CHANGELOG.md` with updated release date.
- **Verification:** `grep "\[0\.4\.0\]" CHANGELOG.md` → `## [0.4.0] - 2026-03-06`.

### Phase C — Quality Gate Runs

- **Inputs:** Current source tree with CHANGELOG update.
- **Actions (in order):**
  1. `make test` — collect test count, coverage %, pass/fail.
  2. `make lint` — confirm 0 ruff errors.
  3. `make format-check` — confirm 0 format errors.
  4. `make typecheck` — confirm 0 mypy errors.
  5. `make doccheck-all` — confirm DocC sync.
  6. `make package-assets-check` — confirm Web UI asset packaging.
- **Outputs:** Validation report with gate results.
- **Verification:** All commands exit 0; coverage ≥ 90%.

### Phase D — Workplan and Next.md Update

- **Inputs:** `SPECS/Workplan.md` P5-T1 entry (status `⬜️ pending`).
- **Actions:**
  - Change `⬜️` to `✅ Completed (2026-03-06)`.
  - Update `SPECS/INPROGRESS/next.md` to list P5-T1 as recently archived.
- **Outputs:** Updated Workplan and next.md.
- **Verification:** `grep "P5-T1" SPECS/Workplan.md` shows `✅ Completed`.

### Phase E — Validation Report

- **Inputs:** Gate output from Phase C.
- **Actions:** Write `SPECS/INPROGRESS/P5-T1_Validation_Report.md`.
- **Outputs:** `P5-T1_Validation_Report.md` with all gate results recorded.

## Manual Release Commands (for human operator post-merge)

After the PR is merged to `main`, the human operator must run the following commands **with PyPI credentials configured** (OIDC via GitHub Actions is the recommended path):

```bash
# 1. Ensure you are on the latest main
git checkout main && git pull origin main

# 2. Create and push the annotated tag
git tag -a v0.4.0 -m "Release 0.4.0 — broker mode, Web UI, auto-restart, tools cache"
git push origin v0.4.0

# 3. The publish-mcp.yml workflow triggers automatically on the v* tag push.
#    Monitor the GitHub Actions run for:
#      - "Publish package to PyPI" step success
#      - "Publish server to MCP Registry" step success

# 4. Verify after publish propagates (~5 min):
pip install mcpbridge-wrapper==0.4.0
uvx mcpbridge-wrapper[webui] --version  # should print 0.4.0

# 5. Check MCP Registry entry:
#    https://registry.modelcontextprotocol.io/?q=Xcode
```

## Notes

- `server.json` version is set by the CI workflow from `${GITHUB_REF#refs/tags/v}` — no manual edit needed before the tag push.
- PyPI publish uses OIDC (`pypa/gh-action-pypi-publish@release/v1`) — no API token management required in the workflow.
- README version badge (`shields.io/pypi/v/mcpbridge-wrapper`) resolves automatically once PyPI has `0.4.0` indexed.
- Docs to update once published: none in this PR scope (badge auto-resolves; CHANGELOG date is the only human-maintained field).
