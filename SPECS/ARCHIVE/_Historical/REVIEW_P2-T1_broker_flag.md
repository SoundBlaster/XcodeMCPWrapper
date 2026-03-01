## REVIEW REPORT — P2-T1: --broker flag

**Scope:** origin/main..HEAD
**Files:** 4 changed (src/__main__.py, README.md, tests/unit/test_main.py, SPECS docs)

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

None.

### Secondary Issues

- **[Low]** `_parse_broker_args` docstring says `--broker-spawn` and `--broker-connect` are "hidden aliases" but they still appear in the README reference section (lines 125-126) as documented legacy options. The word "hidden" may confuse contributors who see them still documented. Suggestion: use "legacy aliases" consistently in the docstring (already done in inline comments; just the docstring header wording).

- **[Nit]** The quick migration example at README lines 133-136 was changed from `--broker-connect` to `--broker`. This is correct for new users but could break copy-paste instructions in existing bookmarks or external guides that showed `--broker-connect` as the quick migration command. No action required — backwards compatibility is maintained — but worth noting for CHANGELOG.

### Architectural Notes

- `--broker` maps exactly to `broker_spawn=True, broker_connect=True` — same as `--broker-spawn`. No `BrokerProxy` logic change was needed because P2-T2 already implemented liveness-aware auto-spawn. This is a clean layering: the CLI surface changed, the underlying machinery did not.
- The return type of `_parse_broker_args` remains `Tuple[bool, bool, bool, list]` — the `broker_spawn` bool now covers both `--broker` and `--broker-spawn`. A future refactor could introduce an enum for clarity, but it's not warranted now.

### Tests

- 4 new unit tests added to `TestParseBrokerArgs` and `TestMainBrokerMode`.
- All 678 unit tests pass.
- Coverage: 91.41% (≥ 90% required). No regression.
- No integration tests needed: the proxy behaviour for `auto_spawn=True` is covered by existing `TestBrokerProxy` tests from P2-T2.

### Next Steps

- No blockers. The "hidden" vs "legacy" wording is a nit and does not require a follow-up task.
- Consider adding `--broker` to CHANGELOG when next release is cut.
