## REVIEW REPORT — broker_owned_listener_guidance

**Scope:** origin/main..HEAD
**Files:** 9

### Summary Verdict
- [x] Approve
- [ ] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

- None.

### Secondary Issues

- None.

### Architectural Notes

- The change stays scoped to PID ownership classification instead of rewriting
  the broader mixed-state guidance flow introduced in `FU-P7-T3-1`.
- Startup and doctor now share the same core rule: only listener PIDs that
  differ from the broker PID should trigger foreign port-conflict guidance.

### Tests

- `pytest tests/unit/test_main.py tests/unit/test_doctor.py -k 'same_pid_listener or broker_owned_listener or mixed_broker_and_foreign_listener_prefers_port_conflict or mixed_state_mentions_foreign_listener'` passed (`6 passed`)
- `pytest tests/unit/test_main.py tests/unit/test_doctor.py` passed (`122 passed`)
- `pytest` passed (`894 passed, 5 skipped`)
- `ruff check src/` passed
- `mypy src/` passed
- `pytest --cov` passed with `91.78%` coverage

### Next Steps

- No follow-up tasks required from this review.
- Archive the review artifact and continue to PR creation.
