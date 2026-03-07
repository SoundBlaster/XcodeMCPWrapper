## REVIEW REPORT — mixed_dashboard_conflict_guidance

**Scope:** origin/main..HEAD
**Files:** 9

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

- [High] `src/mcpbridge_wrapper/__main__.py:613-621`,
  `src/mcpbridge_wrapper/__main__.py:761-779`,
  `src/mcpbridge_wrapper/doctor.py:437-465`:
  the new mixed-state branch treats any listener on the configured dashboard
  port as a foreign port conflict whenever a broker PID is also live. That
  includes the broker daemon’s own listener if it is still bound to the port
  while `/api/control` or `/api/broker/status` is degraded. In that state, the
  new guidance can incorrectly tell users to stop the “existing listener” or
  use `--web-ui-restart`, even though the listener may be the same broker
  process named by the PID file. The fix should distinguish foreign listener
  PIDs from the broker’s own PID before taking the mixed-state port-conflict
  path.

### Secondary Issues

- [Medium] `tests/unit/test_main.py:1788-1824`,
  `tests/unit/test_main.py:2276-2329`,
  `tests/unit/test_doctor.py:313-326`:
  the new regression tests only cover the foreign-listener case. There is no
  test where `listener_pids` equals the broker PID (or contains the local
  doctor PID), so the self-listener misclassification above would currently
  pass unnoticed. Add same-PID coverage alongside the existing foreign-listener
  assertions.

### Architectural Notes

- The task correctly fixed the user-visible blind spot that motivated
  `FU-P7-T3-1`: foreign listeners are now surfaced in the mixed-state path
  instead of being hidden behind broker-reset guidance.
- The remaining issue is about PID ownership precision, not about whether mixed
  state should be surfaced at all. The next iteration should refine the
  classifier to separate foreign listeners from broker-owned listeners.

### Tests

- `pytest tests/unit/test_main.py tests/unit/test_doctor.py -k 'mixed_state_mentions_foreign_listener or mixed_broker_and_foreign_listener_prefers_port_conflict'` passed (`3 passed`)
- `pytest tests/unit/test_main.py tests/unit/test_doctor.py` passed (`119 passed`)
- `pytest` passed (`891 passed, 5 skipped`)
- `ruff check src/` passed
- `mypy src/` passed
- `pytest --cov` passed with `91.64%` coverage

### Next Steps

- Add a focused follow-up task to distinguish foreign listener PIDs from the
  broker’s own PID in startup and doctor mixed-state guidance.
- Add regression coverage for the broker-owned-listener case so the mixed-state
  fix does not regress into self-conflict messaging.
