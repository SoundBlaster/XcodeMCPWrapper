# Validation Report: FU-REBUILD-P10-T1-6

**Task:** Fix uninstall.sh package detection/removal asymmetry and venv cleanup
**Date:** 2026-02-12
**Verdict:** PASS

## Changes Made

### File: `scripts/uninstall.sh`

1. **Detection/removal symmetry fixed:**
   - Detection now stores each detected package name in `DETECTED_PIP_PACKAGES` array
   - Both `mcpbridge-wrapper` and `xcodemcpwrapper` are checked independently
   - Removal iterates over `DETECTED_PIP_PACKAGES`, uninstalling only what is actually installed

2. **Dry-run output fixed:**
   - Dry-run iterates over `DETECTED_PIP_PACKAGES` and runs `pip3 show` for each detected name
   - Accurately reflects which packages would be removed

3. **Venv cleanup added:**
   - Parses `~/bin/xcodemcpwrapper` to detect if it references a `.venv/bin/python*` path
   - Extracts the `.venv` directory path from the wrapper script
   - Shows venv in dry-run, removal summary, and confirmation prompt
   - Removes venv directory during actual uninstall

4. **UX preserved:**
   - `--dry-run`, `--yes`, `--help` flags work identically
   - Confirmation prompt still shown when `--yes` is not passed
   - Clean output format maintained

## Quality Gate Results

| Check | Result |
|-------|--------|
| `python3 -m pytest` | 296 passed, 9 skipped |
| `ruff check src/` | All checks passed |
| `mypy src/mcpbridge_wrapper` | Success: no issues found in 12 source files |
| `bash -n scripts/uninstall.sh` | Syntax OK |

## Acceptance Criteria Verification

- [x] Detection and removal are symmetric: uninstall whichever package name is actually installed (or both)
- [x] Dry-run output accurately reflects which package(s) would be removed
- [x] Script handles the case where package is installed inside a project `.venv`
- [x] Existing UX preserved: dry-run, --yes, confirmation flow, clean output
