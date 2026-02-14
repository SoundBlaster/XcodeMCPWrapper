# BUG-T2 Validation Report

- **Task ID:** BUG-T2
- **Task Name:** codex mcp add with Web UI extras fails in zsh
- **Date:** 2026-02-14
- **Verdict:** PASS

## Scope Validated

- Updated shell command examples using uvx Web UI extras to a zsh-safe quoted form:
  - `uvx --from 'mcpbridge-wrapper[webui]' ...`
- Added explicit troubleshooting guidance for:
  - `zsh: no matches found: mcpbridge-wrapper[webui]`
- Applied updates across user-facing docs and command template text files.

## Acceptance Criteria Check

1. No unquoted shell command examples remain for `uvx --from mcpbridge-wrapper[webui]` in active docs/config text examples.  
   **Result:** PASS
2. Codex setup examples with Web UI extras show a zsh-safe command form.  
   **Result:** PASS
3. Troubleshooting includes exact zsh symptom and fix.  
   **Result:** PASS
4. Required quality gates pass.  
   **Result:** PASS

## Quality Gate Results

- `pytest`  
  - Result: PASS (`345 passed, 5 skipped`)
- `ruff check src/`  
  - Result: PASS (`All checks passed!`)
- `mypy src/`  
  - Result: PASS (`Success: no issues found in 12 source files`)
- `pytest --cov`  
  - Result: PASS (`Total coverage: 96.62%`, required `>= 90%`)

## Notes

- Test runs emitted non-blocking warnings about local port collisions (`127.0.0.1:8080` / `9090`) from background Web UI thread startup in tests; suite still passed and coverage threshold was met.
