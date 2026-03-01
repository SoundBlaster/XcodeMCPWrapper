# Validation Report — P1-T7

**Task:** P1-T7 — Hide README version badge maintenance note
**Date:** 2026-03-01
**Verdict:** PASS

## Checks Run

1. `rg -n "Version badge maintenance" README.md`
   - Result: no matches.
2. `nl -ba README.md | sed -n '1,22p'`
   - Result: version badge block remains present at the top of the README.
3. `pytest -q`
   - Result: pass (669 passed, 18 skipped).
4. `ruff check src/`
   - Result: pass.
5. `mypy src/`
   - Result: pass.
6. `pytest --cov`
   - Result: pass; total coverage 90.92% (>=90%).

## Acceptance Criteria Mapping

- [x] `README.md` no longer contains the exact string `Version badge maintenance: run make badge-version (or make badge-version-check in CI).`
- [x] Version badge remains visible and functional after removing the maintenance note.
