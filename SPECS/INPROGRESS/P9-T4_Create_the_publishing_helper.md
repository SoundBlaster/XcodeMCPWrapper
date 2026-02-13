# P9-T4 — Create the publishing helper

**Task ID:** P9-T4  
**Phase:** Phase 9: Release Management  
**Priority:** P1  
**Dependencies:** P9-T3  
**Status:** Planned

## Objective

Create a publishing helper script that reduces release errors by performing version bumps in all required files from a single command. The helper must validate a provided semantic version, update both `pyproject.toml` and `server.json` consistently, and support `--dry-run` to preview changes safely. It should also print the exact next commands required to complete release publication according to `PUBLISHING.md`.

## Success Criteria

- A helper exists at `scripts/publish_helper.py` and is executable via `python scripts/publish_helper.py <version>`.
- Semantic versions in `MAJOR.MINOR.PATCH` format are accepted; invalid values are rejected with non-zero exit code and clear error.
- Both `pyproject.toml` and `server.json` are updated to the same target version in one run.
- Dry-run mode outputs planned file changes and does not modify files.
- Script output includes next-step release commands for commit/tag/push and notes that GitHub Actions handles publish.
- `PUBLISHING.md` documents helper usage.
- Quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` with coverage >= 90%.

## Test-First Plan

1. Add unit tests covering:
   - valid version updates,
   - invalid version rejection,
   - dry-run no-write behavior,
   - mismatch detection for expected keys and output summary behavior.
2. Implement helper internals to satisfy tests.
3. Update publishing docs and rerun targeted and full test suites.

## Execution Plan

### Phase A: Script Design and CLI Contract
- **Inputs:** `PUBLISHING.md`, `pyproject.toml`, `server.json`
- **Outputs:** CLI arguments and validation rules, parsing/update logic
- **Verification:** `--help` output and unit tests for parser/validator

### Phase B: Implementation and File Updates
- **Inputs:** target version argument and repository files
- **Outputs:** updated `scripts/publish_helper.py`, modified version fields
- **Verification:** tests assert exact replacements and dry-run preservation

### Phase C: Docs and Integration Validation
- **Inputs:** final script behavior
- **Outputs:** updated `PUBLISHING.md`, optional Makefile helper target
- **Verification:** full quality gates and manual dry-run/live-run checks

## Notes

- Keep logic deterministic and avoid external dependencies.
- Fail fast if expected version keys are missing or ambiguous.
- Preserve JSON formatting and TOML readability when writing updates.
