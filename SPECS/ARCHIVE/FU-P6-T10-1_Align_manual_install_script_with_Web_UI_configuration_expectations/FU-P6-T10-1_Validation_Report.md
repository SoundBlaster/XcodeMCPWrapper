# FU-P6-T10-1 Validation Report

**Task:** Align manual install script with Web UI configuration expectations  
**Date:** 2026-02-12  
**Verdict:** PASS

## Changes Implemented

1. Added Web UI install mode to `scripts/install.sh`:
   - `--webui` flag support
   - `--help` output and unknown-arg validation
   - Base install remains default (`pip install -e .`)
   - Web UI mode installs extras (`pip install -e ".[webui]"`)
   - Post-install guidance now states whether Web UI extras are present

2. Updated docs to prevent base/Web UI ambiguity:
   - `README.md`: manual install section now documents `./scripts/install.sh --webui`
   - `README.md`: manual Web UI config snippets now explicitly require Web UI extras
   - `docs/installation.md`: Option D now documents base vs `--webui` mode
   - `docs/troubleshooting.md`: added dedicated symptom/cause/fix for missing Web UI deps (`uvicorn` import error)

## Acceptance Criteria Check

| Criteria | Status | Evidence |
|---|---|---|
| Default `./scripts/install.sh` keeps base behavior | PASS | Installer runs successfully and prints base-only note |
| `./scripts/install.sh --webui` installs Web UI extras | PASS | Installer runs in Web UI mode and prints Web UI deps installed message |
| `xcodemcpwrapper --web-ui --web-ui-port 8080 --help` works in Web UI install mode | PASS | Command exits successfully after `--webui` install |
| Docs no longer imply Web UI works on base-only install | PASS | README/installation/troubleshooting updated with explicit dependency mapping |

## Quality Gates

Environment note:
- Initial `pytest` run with global interpreter failed (`ModuleNotFoundError: mcpbridge_wrapper`).
- Quality gates were rerun in project venv after installing dev/webui extras.

Results in `.venv`:
- `python -m pytest` → **324 passed, 5 skipped**
- `python -m ruff check src/` → **All checks passed**
- `python -m mypy src/` → **Success: no issues found**
- `python -m pytest --cov` → **Coverage 96.62%** (>= 90% requirement)

## Files Modified

- `scripts/install.sh`
- `README.md`
- `docs/installation.md`
- `docs/troubleshooting.md`
