# PRD: FU-P13-T18 — Document unified single-config setup for broker + Web UI multi-agent workflows

## 1. Objective

Document one repeatable setup where multiple AI clients share the same broker and dashboard endpoint without per-client config drift. The goal is to let users keep a single MCP server definition in each client (Cursor, Zed, Claude Code, Codex) that points to a broker-aware command path, while only one broker host process owns `--web-ui` listener startup.

This task builds directly on FU-P13-T17 behavior. Documentation must describe:
- Which process starts and owns the dashboard listener.
- How `--broker-spawn` and `--broker-connect` clients should be configured when using one shared broker host.
- What users should expect when broker MCP transport stays healthy but dashboard endpoint is unavailable.
- How DocC mirrors stay aligned with Markdown docs.

## 2. Success Criteria and Acceptance Tests

### Success Criteria
- `README.md` contains a clear “single-config, shared broker host” quick path and links to detailed docs.
- `docs/broker-mode.md` includes unified config examples for Cursor, Zed, Claude Code, and Codex with explicit host/client roles.
- `docs/webui-setup.md` defines dashboard ownership rules and fallback behavior when the chosen listener is unavailable.
- `docs/troubleshooting.md` adds broker-hosted Web UI diagnostics that distinguish broker health from dashboard reachability.
- Mapped DocC documentation is updated to match user-facing guidance.

### Acceptance Tests
- Verify docs include one end-to-end flow where one process runs broker + Web UI and all other agents use broker connection mode without `--web-ui`.
- Verify docs include explicit expectations for shared dashboard endpoint reuse and port conflict outcomes.
- Verify troubleshooting steps include concrete commands (`lsof`, broker host start/restart checks, endpoint verification).

## 3. Test-First Plan

1. Review current behavior coverage to ensure docs claims are already validated by tests from FU-P13-T17 and prior broker-mode work.
2. Add/adjust tests only if a new behavior statement lacks evidence in existing test suite.
3. Run required quality gates after documentation updates:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

## 4. Execution Plan (Hierarchical TODO)

### Phase A — Behavior and config alignment
- Inputs: runtime behavior from `src/mcpbridge_wrapper/__main__.py`, broker and Web UI docs.
- Outputs: authoritative wording for broker host ownership and multi-agent shared endpoint semantics.
- Verification: no docs claim behavior that code does not implement.

### Phase B — Documentation and examples
- Inputs: `README.md`, `docs/broker-mode.md`, `docs/webui-setup.md`, `docs/troubleshooting.md`.
- Outputs: unified single-config examples, ownership matrix, fallback and diagnostics guidance.
- Verification: examples are internally consistent and use current CLI flags.

### Phase C — DocC synchronization
- Inputs: mapped files under `Sources/XcodeMCPWrapper/Documentation.docc/`.
- Outputs: mirrored guidance aligned with Markdown docs.
- Verification: key sections and commands match without contradictions.

### Phase D — Validation report
- Inputs: edited docs and gate outputs.
- Outputs: `SPECS/INPROGRESS/FU-P13-T18_Validation_Report.md` with verdict and acceptance criteria checks.
- Verification: report records all required gates and result status.

## 5. Decision Points and Constraints

- Preserve compatibility with existing single-agent quick start instructions.
- Do not imply automatic dashboard failover or multi-owner listener support.
- Keep commands copy/paste-ready and avoid introducing unsupported CLI flags.
- Review subject for REPORT step: `fu_p13_t18_unified_config_docs`.

## 6. Notes (Files likely touched)

- `README.md`
- `docs/broker-mode.md`
- `docs/webui-setup.md`
- `docs/troubleshooting.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/tutorials/broker-mode.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/tutorials/webui-setup.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/tutorials/troubleshooting.md`
