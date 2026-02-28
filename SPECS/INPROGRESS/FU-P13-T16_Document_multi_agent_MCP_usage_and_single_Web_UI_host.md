# PRD: FU-P13-T16 — Document multi-agent MCP usage and single Web UI host

## 1. Objective

Improve user-facing documentation so multi-agent MCP behavior is predictable and operable. The task clarifies that Web UI is not a separate service by default; it is hosted by one wrapper process that successfully binds a specific `host:port`. In multi-agent environments (Zed/Cursor/Claude/Codex starting separate wrapper instances), multiple processes may attempt to start Web UI on the same port, and non-host processes will continue MCP bridging while dashboard startup is skipped.

The documentation must establish a recommended topology: one dedicated broker/Web UI host process and client processes using `--broker-connect`. It must also provide direct-mode alternatives (single Web UI owner, unique ports per process) and concrete diagnostics for “tools are green, dashboard unavailable.”

## 2. Success Criteria and Acceptance Tests

### Success Criteria
- Multi-agent guidance is explicit in `README.md` and links to deeper broker/Web UI docs.
- `docs/broker-mode.md` defines dedicated host + client proxy setup with concrete commands.
- `docs/webui-setup.md` and `docs/troubleshooting.md` explain Web UI ownership semantics and conflict behavior.
- All quality gates pass and coverage remains at or above project threshold.

### Acceptance Tests
- Validate docs contain at least one end-to-end example where only the host uses `--web-ui` and clients use `--broker-connect`.
- Validate docs include direct-mode guidance for multiple agents without broker mode.
- Validate troubleshooting includes listener ownership checks (`lsof`) and recovery options (`--web-ui-restart`, alternate port, dedicated host).

## 3. Test-First Plan

1. Add/update unit tests that lock in any behavior statements referenced by documentation if assertions are missing.
2. If runtime behavior is already tested, avoid new tests and instead verify existing tests still cover described semantics.
3. Run required quality gates in full:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

## 4. Execution Plan (Hierarchical TODO)

### Phase A — Source-of-truth alignment
- Inputs: existing CLI/runtime behavior in `src/mcpbridge_wrapper/__main__.py`, `src/mcpbridge_wrapper/webui/server.py`.
- Outputs: validated behavior statements for port collision and startup skip behavior.
- Verification: docs assertions map to observed code paths and current warnings.

### Phase B — Documentation updates
- Inputs: `README.md`, `docs/broker-mode.md`, `docs/webui-setup.md`, `docs/troubleshooting.md`.
- Outputs: updated multi-agent sections, recommended topology commands, direct-mode fallback, and diagnostics.
- Verification: link integrity, command consistency, no conflicting guidance.

### Phase C — Validation artifacts
- Inputs: updated docs + gate results.
- Outputs: `SPECS/INPROGRESS/FU-P13-T16_Validation_Report.md` with PASS/FAIL verdict and evidence.
- Verification: report includes command results and explicit acceptance criteria checks.

## 5. Decision Points and Constraints

- Constraint: preserve backward-compatible single-client setup instructions.
- Constraint: avoid claiming behavior not implemented in code (for example automatic Web UI failover between processes).
- Decision: use `FU-P13-T16` review subject `fu_p13_t16_multi_agent_mcp_docs` for report naming consistency.

## 6. Notes (Docs to update)

- `README.md`
- `docs/broker-mode.md`
- `docs/webui-setup.md`
- `docs/troubleshooting.md`
