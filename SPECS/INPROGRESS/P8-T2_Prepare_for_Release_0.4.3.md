# P8-T2: Prepare for Release 0.4.3

**Status:** In Progress
**Date:** 2026-03-10
**Priority:** P0
**Dependencies:** P1-T13, P2-T8 (completed)

---

## Objective

Prepare patch release `0.4.3` for the work merged after `v0.4.2`:
- `P2-T8` hardened broker startup by gating `tools/list` on a warmed tool catalog and retrying the probe instead of exposing a transient empty catalog to clients.
- `P1-T13` documented the editable-install version mismatch trap so local development setups can self-diagnose stale `.venv` metadata after a version bump.

The deliverable is a merge-ready branch that updates release metadata, records release notes in `CHANGELOG.md`, passes the full pre-release quality gate suite, and leaves exact post-merge tag/publish commands for the human operator.

**Scope boundary:** Creating and pushing the `v0.4.3` tag, publishing to PyPI, and publishing to the MCP Registry remain post-merge human actions on `main`. This task prepares the branch and validates the repository state before those actions.

---

## Current State

| Artifact | Current value |
|----------|---------------|
| `pyproject.toml` version | `0.4.2` |
| `server.json` root version | `0.4.2` |
| `server.json` package version | `0.4.2` |
| `README.md` version badge | `v0.4.2` |
| Latest git tag on current baseline | `v0.4.2` |
| Unreleased merged work since `v0.4.2` | `P2-T8`, `P1-T13` |

---

## Deliverables

1. **`pyproject.toml`** — `[project].version` updated to `0.4.3`.
2. **`server.json`** — root `version` and `packages[0].version` updated to `0.4.3`.
3. **`README.md`** — version badge updated to `v0.4.3`.
4. **`CHANGELOG.md`** — new `[0.4.3] - 2026-03-10` entry summarizing the shipped fixes/docs.
5. **`SPECS/INPROGRESS/P8-T2_Validation_Report.md`** — records release metadata checks, quality gates, and post-merge publish instructions.

---

## Implementation Steps

### 1. Update release metadata

Use the existing release helpers so version fields stay in sync:

```bash
make bump-version VERSION=0.4.3
make badge-version TAG=v0.4.3
```

This updates:
- `pyproject.toml`
- `server.json`
- `README.md` version badge block

### 2. Add release notes

Update `CHANGELOG.md` with a new `0.4.3` entry that covers:
- broker `tools/list` warm-catalog gating / retry behavior (`P2-T8`)
- the editable-install troubleshooting addition (`P1-T13`)

### 3. Run pre-release quality gates

Run the full local validation suite required by FLOW, `CONTRIBUTING.md`, and this release workflow:

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

Write `SPECS/INPROGRESS/P8-T2_Validation_Report.md` with:
- the exact versions now present in release metadata
- changelog verification
- quality gate outcomes
- explicit post-merge steps for tagging and publish verification

### 5. Post-merge operator steps

These commands must be executed only after the PR merges into `main`:

```bash
git checkout main
git pull origin main
git tag v0.4.3
git push origin v0.4.3
```

Then verify:
- GitHub Actions `publish-mcp.yml` succeeds for `v0.4.3`
- PyPI serves `mcpbridge-wrapper==0.4.3`
- the MCP Registry reflects `0.4.3`

---

## Acceptance Criteria

- [ ] `pyproject.toml` contains `version = "0.4.3"`.
- [ ] `server.json` root `version` and `packages[0].version` both equal `0.4.3`.
- [ ] `README.md` version badge reflects `v0.4.3`.
- [ ] `CHANGELOG.md` contains `[0.4.3] - 2026-03-10` and summarizes `P2-T8` and `P1-T13`.
- [ ] `pytest tests/ -v --cov=src --cov-report=term` passes with coverage ≥90%.
- [ ] `python -m ruff check src/ tests/` passes.
- [ ] `python -m ruff format --check src/ tests/` passes.
- [ ] `mypy src/` passes.
- [ ] `make doccheck-all` passes.
- [ ] `python -m build` and `twine check dist/*` pass.
- [ ] Validation report captures the exact post-merge commands and verification steps for `v0.4.3`.

---

## Risk Notes

- `main` is protected. Do not tag or publish from this feature branch; tag only after merge.
- `make badge-version` must be called with explicit `TAG=v0.4.3` so it does not reuse `v0.4.2`.
- If the local editable install was not refreshed after the version bump, local `mcpbridge-wrapper --version` output may lag until `pip install -e .` is rerun. This is documented by `P1-T13`.
