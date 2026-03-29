# PRD: P1-T14 — Document Codex Desktop resource-probe behavior for Xcode tools MCP connectivity

## Status

In Progress

## Objective Summary

Codex Desktop can issue MCP resource-discovery probes (`resources/list`,
`resources/templates/list`) even when connected to a tools-focused server such as
Xcode MCP. In this integration, those resource methods may return `-32601
unknown method` while Xcode tool calls work normally. Current docs mention
resource-probe edge cases but do not provide a clear, user-facing interpretation
or a deterministic health-check workflow for Codex Desktop users.

This task updates README, troubleshooting, and Codex setup docs (plus DocC
mirrors) to state that resource-probe `-32601` can be non-fatal, and to direct
users to validate connectivity using actual Xcode tool calls.

## Success Criteria and Acceptance Tests

- Docs explicitly call out expected Codex Desktop resource-probe behavior:
  `resources/list` and `resources/templates/list` may return `-32601`.
- Docs clearly distinguish:
  - non-fatal resource-probe errors
  - real tool-transport failures.
- Verification guidance points to concrete tool calls (`XcodeListWindows`,
  `XcodeLS`) as source-of-truth checks.
- README and DocC overview known-issues sections stay aligned.
- Troubleshooting and Codex setup Markdown/DocC mirrors stay aligned.
- Validation run records required quality gates and outcomes.

## Test-First Plan

1. Inspect current docs and DocC mirrors for sections that describe:
   - Codex behavior
   - resource-probe errors
   - connection verification.
2. Draft wording updates in docs first, then mirror equivalent guidance in DocC.
3. Run repository quality gates and documentation consistency checks.
4. Record exact command outputs in the validation report.

## Hierarchical TODO Plan

### Phase 1: Scope and Message Design

- Inputs:
  - `README.md`
  - `docs/troubleshooting.md`
  - `docs/codex-setup.md`
  - corresponding DocC mirrors.
- Outputs:
  - final wording for non-fatal `-32601` behavior and tool-call verification.
- Verification:
  - all three documentation surfaces contain consistent interpretation and
    actionable next steps.

### Phase 2: Documentation and Mirror Updates

- Inputs:
  - approved wording from Phase 1.
- Outputs:
  - updated Markdown docs:
    - `README.md`
    - `docs/troubleshooting.md`
    - `docs/codex-setup.md`
  - updated DocC mirrors:
    - `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`
    - `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`
    - `Sources/XcodeMCPWrapper/Documentation.docc/CodexCLISetup.md`
- Verification:
  - each Markdown update has corresponding DocC mirror content where applicable.

### Phase 3: Validation and Workflow Artifacts

- Inputs:
  - updated docs and mirrors.
- Outputs:
  - `SPECS/INPROGRESS/P1-T14_Validation_Report.md`.
- Verification:
  - required gates pass:
    - `pytest`
    - `ruff check src/`
    - `mypy src/`
    - `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`
  - documentation consistency check passes:
    - `make doccheck-all`.

## Decision Points and Constraints

- Constraint: preserve semantics for existing known issues while adding Codex
  Desktop-specific clarification.
- Constraint: avoid implying server failure when only resource probes fail.
- Decision: treat tool-call success as canonical connectivity evidence for this
  server type.

## Notes

- Keep troubleshooting guidance concrete and concise.
- Keep setup docs focused on operator actions, not protocol theory.
- Ensure archive and review artifacts reflect FOLLOW-UP skip if no actionable
  findings are discovered.
