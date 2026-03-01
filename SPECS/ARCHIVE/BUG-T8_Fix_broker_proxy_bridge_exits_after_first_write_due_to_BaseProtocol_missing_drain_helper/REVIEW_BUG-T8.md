# REVIEW: BUG-T8 — Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper

**Reviewer:** Claude Sonnet 4.6
**Date:** 2026-03-01
**Branch:** `codex/feature/BUG-T8-fix-broker-proxy-stdout-writer`
**Verdict:** ✅ Approve

---

## Summary

BUG-T8 fixes a silent protocol mismatch that caused `BrokerProxy` to exit after
the first write in every `--broker-spawn` / `--broker-connect` session. Root cause
was correctly identified, fix is minimal and correct, quality gates pass, and a
pre-existing test isolation flaw was repaired as a bonus.

---

## Findings

### 1. Fix correctness — PASS

`asyncio.StreamReaderProtocol` is the standard asyncio pattern for wrapping a
write pipe as a `StreamWriter` because it inherits `FlowControlMixin._drain_helper`.
Using the same reader/protocol/transport triple that `asyncio.open_connection`
uses internally is the right approach and matches CPython guidance.

### 2. Test isolation fix — PASS

Using a `tempfile.mkdtemp()` socket path in `TestBrokerProxyBasic.setup_method`
removes the environmental dependency on `~/.mcpbridge_wrapper/broker.sock`. The
fix is surgical and correct.

### 3. Quality gates — PASS

| Gate | Result |
|------|--------|
| pytest (715 tests) | ✅ Pass |
| ruff check | ✅ Pass |
| mypy (18 files) | ✅ Pass |
| coverage | ✅ 91.61% |

### 4. proxy.py coverage note (non-blocking)

`proxy.py` line coverage is 76.2% — the uncovered lines are the
`_make_stdin_reader` / `_make_stdout_writer` pipe-attach paths and some error
branches. These are integration-only paths (require real file descriptors) and
are not easily unit-testable without a subprocess harness. Acceptable for now.

### 5. No doc changes needed

The fix is internal to the broker proxy; no user-facing documentation change is
required.

---

## Actionable Findings

None. All acceptance criteria satisfied.

---

## Follow-up Recommendations (non-blocking)

- Consider adding a subprocess-based integration test for the full proxy pipeline
  (initialize → tools/list through a real broker socket) to prevent regression of
  this exact failure pattern. This is optional and can be a separate task.

---

## Verdict: ✅ Approve

No blocking issues. Ready for PR.
