## REVIEW REPORT — P2-T3: spawn lock

**Scope:** origin/main..HEAD
**Files:** 2 changed (src/broker/proxy.py, tests/unit/test_broker_proxy.py)

### Summary Verdict
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

None.

### Secondary Issues

- **[Low]** The lock is held across `await asyncio.sleep(0.2)` inside the poll loop. Since `flock` was acquired via `run_in_executor` and is held on a thread-pool fd, the poll loop's `await asyncio.sleep` yields the event loop normally — but other async tasks on the same event loop can still run. This is correct behaviour (the lock serialises OS-level processes, not coroutines), but the docstring could make this clearer for future readers.

- **[Low]** `open(lock_file, "w")` truncates the file on each open. Two concurrent openers both succeed (POSIX open is not exclusive by default) and then the flock serialises them. This is intentional and correct, but "w" mode could confuse reviewers who expect exclusive open. A brief inline comment `# "w" mode is fine; flock(LOCK_EX) serialises concurrent openers` would clarify intent.

- **[Nit]** `import subprocess` inside the `with` block is a deferred import for a module already used elsewhere in the project. Not harmful, but minor inconsistency with the rest of `proxy.py` import style.

### Architectural Notes

- The double-check pattern (check liveness → take lock → re-check liveness) correctly eliminates the TOCTOU window. Any process that wins the lock and finds a live broker immediately returns; any that finds it absent spawns exactly one daemon.
- `flock` semantics on macOS: automatic release on fd close (including SIGKILL) makes the lock stale-proof. No cleanup file is needed.
- The lock file `broker.lock` is derived from `pid_file.with_suffix(".lock")` — cleanly co-located with existing runtime files and auto-cleaned when `~/.mcpbridge_wrapper/` is wiped.

### Tests

- 4 new tests in `TestBrokerProxySpawnLock`. All pass.
- All 682 unit tests pass; no regression.
- Coverage: 91.43% (≥ 90%). Proxy.py coverage slightly lower due to async path branching — acceptable.
- No integration test for true concurrent OS-level race; the sequential simulation in `test_second_proxy_skips_spawn_after_first_succeeds` is sufficient for verifying the re-check logic.

### Next Steps

- The "w" mode comment nit is optional; no follow-up task needed.
- No actionable issues → FOLLOW-UP skipped.
