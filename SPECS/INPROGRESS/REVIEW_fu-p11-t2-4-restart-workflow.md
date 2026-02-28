## REVIEW REPORT — FU-P11-T2-4 restart workflow

**Scope:** origin/main..HEAD
**Files:** 10

### Summary Verdict
- [x] Approve
- [ ] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues
- None.

### Secondary Issues
- [Low] `lsof` dependency is macOS-standard in this repository context; behavior remains deterministic when unavailable (restart helper no-ops), and tests cover fallback paths.

### Architectural Notes
- Restart logic is isolated into helpers (`_find_listener_pids_for_port`, `_terminate_pids_gracefully_then_force`, `_restart_webui_listener`) to keep `main()` readable and testable.
- Existing non-restart startup behavior remains unchanged.

### Tests
- Quality gates executed and passing:
  - `PYTHONPATH=src pytest`
  - `PYTHONPATH=src ruff check src/`
  - `PYTHONPATH=src mypy src/`
  - `PYTHONPATH=src pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`
- Coverage remains >= 90%: 90.89%.

### Next Steps
- No actionable follow-up tasks identified.
- FOLLOW-UP step can be skipped for this task.
