# P8-T3: Prepare for Release 0.4.4

**Status:** In Progress
**Date:** 2026-03-10
**Priority:** P0
**Dependencies:** T-010, T-011 (completed)

---

## Objective

Prepare patch release `0.4.4` for the work merged after `v0.4.3`:
- `T-010` added a deterministic Xcode approval observation harness so startup behavior around the Xcode "Allow" dialog can be captured and replayed as structured protocol traces.
- `T-011` taught the broker to emit a synthetic `notifications/tools/list_changed` when the warmed tool catalog first becomes usable, compensating for missing upstream change notifications after Xcode approval.

The deliverable is a merge-ready branch that updates release metadata, records release notes in `CHANGELOG.md`, passes the full pre-release quality gate suite required by `PUBLISHING.md`, and leaves exact post-merge tag/publish commands for the human operator.

**Scope boundary:** Creating and pushing the `v0.4.4` tag, publishing to PyPI, and publishing to the MCP Registry remain post-merge human actions on `main`. This task prepares the branch and validates the repository state before those actions.

---

## Current State

| Artifact | Current value |
|----------|---------------|
| `pyproject.toml` version | `0.4.3` |
| `server.json` root version | `0.4.3` |
| `server.json` package version | `0.4.3` |
| `README.md` version badge | `v0.4.3` |
| `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` version badge | `v0.4.3` |
| Latest git tag on current baseline | `v0.4.3` |
| Unreleased merged work since `v0.4.3` | `T-010`, `T-011` |

---

## Deliverables

1. **`pyproject.toml`** — `[project].version` updated to `0.4.4`.
2. **`server.json`** — root `version` and `packages[0].version` updated to `0.4.4`.
3. **`README.md`** — version badge updated to `v0.4.4`.
4. **`Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`** — DocC overview badge updated to `v0.4.4`.
5. **`CHANGELOG.md`** — new `[0.4.4] - 2026-03-10` entry summarizing the shipped tooling/runtime changes.
6. **`SPECS/INPROGRESS/P8-T3_Validation_Report.md`** — records release metadata checks, quality gates, and post-merge publish instructions.

---

## Implementation Steps

### 1. Update release metadata

Use the existing release helpers so version fields stay in sync:

```bash
make bump-version VERSION=0.4.4
make badge-version TAG=v0.4.4
python scripts/update_version_badge.py --readme Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md --tag v0.4.4
```

This updates:
- `pyproject.toml`
- `server.json`
- `README.md` version badge block
- `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` version badge block

### 2. Add release notes

Update `CHANGELOG.md` with a new `0.4.4` entry that covers:
- the Xcode approval observation harness and its troubleshooting/docs value (`T-010`)
- the broker-side synthetic `notifications/tools/list_changed` signal after warm-up (`T-011`)

### 3. Run pre-release quality gates

Run the full local validation suite required by FLOW and `PUBLISHING.md`:

```bash
pytest tests/ -v --cov=src --cov-report=term
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
mypy src/
make doccheck-all
python -m build
twine check dist/*
```

### 4. Record release validation

Write `SPECS/INPROGRESS/P8-T3_Validation_Report.md` with:
- the exact versions now present in release metadata
- changelog verification
- quality gate outcomes
- explicit post-merge steps for tagging and publish verification

### 5. Post-merge operator steps

These commands must be executed only after the PR merges into `main`:

```bash
git checkout main
git pull origin main
git tag v0.4.4
git push origin v0.4.4
```

Then verify:
- GitHub Actions `publish-mcp.yml` succeeds for `v0.4.4`
- PyPI serves `mcpbridge-wrapper==0.4.4`
- the MCP Registry reflects `0.4.4`

---

## Acceptance Criteria

- [ ] `pyproject.toml` contains `version = "0.4.4"`.
- [ ] `server.json` root `version` and `packages[0].version` both equal `0.4.4`.
- [ ] `README.md` and `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` version badges reflect `v0.4.4`.
- [ ] `CHANGELOG.md` contains `[0.4.4] - 2026-03-10` and summarizes `T-010` and `T-011`.
- [ ] `pytest tests/ -v --cov=src --cov-report=term` passes with coverage >=90%.
- [ ] `python -m ruff check src/ tests/` passes.
- [ ] `python -m ruff format --check src/ tests/` passes.
- [ ] `mypy src/` passes.
- [ ] `make doccheck-all` passes.
- [ ] `python -m build` and `twine check dist/*` pass.
- [ ] Validation report captures the exact post-merge commands and verification steps for `v0.4.4`.

---

## Risk Notes

- `main` is protected. Do not tag or publish from this feature branch; tag only after merge.
- `make badge-version` must be called with explicit `TAG=v0.4.4` so it does not reuse `v0.4.3`.
- The release notes must stay scoped to work already merged after `v0.4.3`; do not pull in unmerged follow-ups or future publish verification results.

---
**Archived:** 2026-03-10
**Verdict:** PASS
