# Next Task: P1-T13

## Selected Task

- **ID:** P1-T13
- **Name:** Document stale editable install version mismatch in troubleshooting guide
- **Priority:** P2
- **Branch:** `feature/P1-T13-stale-editable-install-troubleshooting`
- **Status:** In Progress

## Description

When developing locally, the `.venv` editable install records the package version at install time in its `dist-info` directory. If `pyproject.toml` is bumped to a new version without re-running `pip install -e .`, the `mcpbridge-wrapper` command in the dev PATH still reports the old version. This causes `--doctor` to show a version mismatch between the running broker (started via `uvx`, which fetches the latest from PyPI) and the local binary.

Document this scenario, its cause, and the fix in `docs/troubleshooting.md` and sync the DocC mirror.

## Outputs

- `docs/troubleshooting.md` — new entry for stale editable install version mismatch
- `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` — DocC mirror synced

## Recently Archived

- `2026-03-10` — `P2-T8` archived with verdict `PASS`
- `2026-03-07` — `P8-T1` archived with verdict `PASS`
- `2026-03-07` — `P7-T5` archived with verdict `PASS`
- `2026-03-07` — `P7-T4` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T3-2` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T3-1` archived with verdict `PASS`
