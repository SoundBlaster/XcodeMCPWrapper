# P1-T12 — Improve Troubleshooting Docs for Zed Broker Startup Timeouts

**Task ID:** P1-T12
**Priority:** P1
**Phase:** Phase 1 — Documentation
**Status:** In Progress

## Objective Summary

Extend the broker troubleshooting guidance with the Zed-specific failure mode observed during live
testing: after approving the first `mcpbridge-broker` Xcode dialog, Zed can briefly show a green
context-server indicator with 0 tools and later fail on reconnect with `Context server request timeout`.
The current docs explain the first-approval race in general terms, but they do not give Zed users a
clear recovery path once the broker state becomes stale or once Zed starts timing out on `initialize`
or `tools/list`.

This task should document the practical recovery that worked in session:
- stop the stale broker daemon
- start a dedicated `--broker-daemon` host manually
- re-enable the Zed context server after the host is already available

It should also clarify that multiple inactive `mcpbridge-broker` rows in Xcode Agent Activity usually
represent historical broker sessions or retries, not multiple live broker daemons competing at once.

## Success Criteria and Acceptance Tests

- `docs/troubleshooting.md` explicitly describes the Zed sequence of `0 tools` after approval followed
  by `Context server request timeout` on subsequent reconnects.
- `docs/troubleshooting.md` includes a dedicated-host recovery sequence using:
  - `mcpbridge-wrapper --broker-stop`
  - manual `--broker-daemon` startup
  - re-enabling the Zed context server after the daemon is healthy
- `docs/troubleshooting.md` explains how to interpret inactive `mcpbridge-broker` entries in Xcode
  Agent Activity.
- `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` mirrors the same guidance.
- Documentation sync check passes.

Acceptance test procedure:
1. Read the updated troubleshooting entry and confirm a Zed user can recover without guessing.
2. Verify the dedicated-host commands are correct for the wrapper CLI.
3. Run `make doccheck` to ensure the markdown and DocC mirror stay aligned.

## Test-First Plan

Before editing docs:
1. Inspect the current troubleshooting sections for broker cold-start and Zed references.
2. Confirm the exact command forms already documented for `--broker-stop` and `--broker-daemon`.
3. Identify the matching DocC section so the prose can be mirrored without drift.

After editing docs:
1. Run `make doccheck`.
2. Run the repository quality gates required by FLOW:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov`
3. Capture outcomes in `SPECS/INPROGRESS/P1-T12_Validation_Report.md`.

## TODO Plan

### Phase 1 — Analyze Current Gaps
- **Inputs:** existing `docs/troubleshooting.md`, DocC troubleshooting mirror, Zed/Xcode behavior observed during debugging
- **Outputs:** exact insertion points and missing recovery details
- **Verification:** the gap list covers timeout recovery, dedicated-host guidance, and Xcode Agent Activity interpretation

### Phase 2 — Update User-Facing Documentation
- **Inputs:** approved task scope and verified commands
- **Outputs:** updated troubleshooting markdown plus synced DocC mirror
- **Verification:** both files describe the same Zed recovery path and use correct command examples

### Phase 3 — Validate and Record
- **Inputs:** changed docs and repository quality commands
- **Outputs:** validation report with doccheck and quality gate results
- **Verification:** checks complete successfully and acceptance criteria are marked with evidence

## Decision Points and Constraints

- Keep this task focused on troubleshooting and recovery, not on broker code changes.
- Prefer recovery steps that reduce Zed startup timing sensitivity; dedicated-host mode is the key
  recommendation for this scenario.
- Mirror the docs faithfully in DocC rather than introducing diverging wording or extra claims.

## Notes

- Update only the troubleshooting docs unless another file is necessary to avoid ambiguity.
- Preserve existing first-approval guidance from P1-T10 and add the Zed timeout recovery as an
  extension of that known issue rather than a conflicting explanation.
