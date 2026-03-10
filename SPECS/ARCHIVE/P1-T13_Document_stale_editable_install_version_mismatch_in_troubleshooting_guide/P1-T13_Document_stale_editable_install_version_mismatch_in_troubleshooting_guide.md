# PRD: P1-T13 — Document stale editable install version mismatch in troubleshooting guide

## Status

In Progress

## Problem

When a developer works in the local repository with `.venv` activated (or with `.venv/bin` on PATH), the `mcpbridge-wrapper` command resolves to the editable install inside `.venv`. The version metadata for that install is recorded in `.venv/lib/pythonX.Y/site-packages/mcpbridge_wrapper-{VERSION}.dist-info/` at the time `pip install -e .` was last run.

If `pyproject.toml` is subsequently bumped to a new version (e.g. `0.4.1` → `0.4.2`) without re-running `pip install -e .`, the dist-info still reports the old version. As a result:

- `mcpbridge-wrapper --doctor` shows `Package Version: 0.4.1`
- A broker daemon started via `uvx --from mcpbridge-wrapper` (which fetches fresh from PyPI) writes version `0.4.2` to `broker.version`
- `--doctor` detects a "version mismatch" and prompts the user to restart the broker
- The user is confused: they just released `0.4.2`, but their own dev environment reports `0.4.1`

This is a pure developer environment issue — end users on `uvx` are never affected — but it can trap contributors and maintainers who have the repo `.venv` active in their shell.

## Deliverables

1. **`docs/troubleshooting.md`** — new section under a "Development / Local Repository" heading (or appended to an existing relevant section) that:
   - Names the symptom: `--doctor` reports a version mismatch between local binary (`0.4.N`) and broker (`0.4.N+1`)
   - Explains the root cause: stale `dist-info` from an old `pip install -e .` after `pyproject.toml` was bumped
   - Provides the one-line fix: `.venv/bin/pip install -e .` (or `pip install -e .` with venv active)
   - Notes that `uvx` always fetches the latest PyPI release independently of the local `.venv`

2. **`Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`** — DocC mirror synced to match the new section.

## Acceptance Criteria

- [ ] `docs/troubleshooting.md` describes the symptom, root cause (stale editable dist-info), and the fix (`pip install -e .`)
- [ ] The entry explains that `uvx` fetches from PyPI independently of the `.venv` editable install
- [ ] DocC mirror updated to match
- [ ] `make doccheck-all` passes (mirrors in sync)

## Out of Scope

- No code changes — documentation only
- No changes to `--doctor` output format
- End-user (non-dev) scenarios are already covered by existing version-mismatch entries

## Dependencies

None

## Risk

Low — documentation-only change.

---
**Archived:** 2026-03-10
**Verdict:** PASS
