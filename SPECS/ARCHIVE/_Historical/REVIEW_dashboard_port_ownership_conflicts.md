## REVIEW REPORT — dashboard_port_ownership_conflicts

**Scope:** origin/main..HEAD
**Files:** 11

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

None.

### Secondary Issues

- [Medium] `src/mcpbridge_wrapper/__main__.py:604-640`,
  `src/mcpbridge_wrapper/__main__.py:1072-1080`:
  `_report_requested_dashboard_unavailable()` prioritizes
  `running_broker_pid` over `listener_pids`. In the mixed state where a broker
  PID is still live but the requested dashboard port is actually occupied by an
  unrelated listener, both `--broker-console` and `--broker-daemon --web-ui`
  will tell users to reset the broker first and omit the foreign port owner.
  That remediation can loop back into the same conflict because the real
  blocker, the non-broker listener on the port, was never surfaced. The
  conflict classifier should prefer observable foreign port ownership or name
  both blockers in one explicit recovery path.

### Architectural Notes

- The task correctly removes the most confusing partial state: explicit
  dashboard startup no longer silently degrades into “broker alive, dashboard
  absent”.
- Keeping `--broker-console --web-ui-restart` as the safe recovery path is the
  right product choice; the remaining issue is about mixed-state prioritization,
  not the core startup contract.
- Coverage-reference updates were kept in lockstep across README and the DocC
  mirror, which avoids a repeat of the earlier documentation drift problem.

### Tests

- `pytest tests/unit/test_main.py tests/unit/test_main_tui.py tests/unit/test_doctor.py tests/unit/test_tui.py` passed (`163 passed`)
- `pytest` passed (`887 passed, 5 skipped`)
- `python -m ruff check src/ tests/` passed
- `mypy src/` passed
- `make format-check` passed
- `python scripts/check_doc_sync.py --all --require-same-commit` passed
- `pytest --cov=src --cov-report=term` passed with `91.62%` coverage

### Next Steps

- Add a focused follow-up task to improve mixed-state conflict prioritization
  when a live broker PID and a foreign dashboard-port listener are both
  observable.
