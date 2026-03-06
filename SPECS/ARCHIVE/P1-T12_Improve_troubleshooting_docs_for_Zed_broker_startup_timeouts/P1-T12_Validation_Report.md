# P1-T12 Validation Report

**Task:** Improve troubleshooting docs for Zed broker startup timeouts
**Date:** 2026-03-07
**Verdict:** PASS

## Acceptance Criteria Checklist

- [x] `docs/troubleshooting.md` documents the Zed sequence of green/0 tools after approval followed by `Context server request timeout` on restart
  - Added a Zed-specific escalation subsection under the existing broker first-approval troubleshooting entry
  - The new text explains why Zed can move from green/0 tools to a red timeout state after the initial approval race

- [x] `docs/troubleshooting.md` includes a step-by-step dedicated-host recovery flow using `mcpbridge-wrapper --broker-stop` and manual `--broker-daemon` startup
  - Recovery steps now instruct users to disable Zed, stop the stale broker, start a dedicated broker host manually, verify with `--broker-status`, then re-enable Zed

- [x] `docs/troubleshooting.md` explains that inactive `mcpbridge-broker` entries in Xcode Agent Activity are usually historical sessions, not proof of multiple live brokers
  - Added an explicit Xcode Agent Activity note describing inactive broker rows as previous sessions or reconnect attempts

- [x] `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` mirrors the new guidance
  - Added the matching DocC section `Zed reconnects with "Context server request timeout" after first approval`

## Quality Gates

- [x] `make doccheck`
- [x] `ruff check src/`
- [x] `mypy src/`
- [x] `pytest`
- [x] `pytest tests/ -v --cov=src --cov-report=term --cov-report=xml`
- [x] `make doccheck-all`

## Command Results

| Command | Result |
|---------|--------|
| `make doccheck` | PASS |
| `ruff check src/` | PASS |
| `mypy src/` | PASS |
| `pytest` | PASS in repo `.venv` (`785 passed, 5 skipped`) |
| `pytest tests/ -v --cov=src --cov-report=term --cov-report=xml` | PASS, coverage `90.81%` |
| `make doccheck-all` | PASS |

## Files Modified

| File | Change |
|------|--------|
| `docs/troubleshooting.md` | Added Zed-specific timeout recovery and Xcode Agent Activity clarification |
| `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` | Mirrored the new Zed recovery guidance |

## Notes

- The shell-global `pytest` invocation initially failed because the package was not importable outside
  an editable install. Validation was rerun in the repository's existing `.venv` after:

```bash
source .venv/bin/activate
python -m pip install -e '.[webui]'
```

- This task changed documentation only. No application source or test files required modification.
