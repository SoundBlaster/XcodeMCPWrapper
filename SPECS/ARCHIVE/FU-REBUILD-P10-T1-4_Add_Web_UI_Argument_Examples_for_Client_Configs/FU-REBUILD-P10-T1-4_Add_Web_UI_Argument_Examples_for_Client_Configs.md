# PRD — FU-REBUILD-P10-T1-4 Add Web UI Argument Examples for Client Configs

## Objective Summary
The goal of this follow-up task is to close the documentation gap for enabling the optional Web UI dashboard when configuring MCP clients. Existing docs and config examples show the base wrapper command but do not consistently include argument examples for `--web-ui` and `--web-ui-port`. This creates avoidable setup friction for users who want audit logs, live metrics, and request inspection from day one.

This task updates client-facing configuration examples for Zed, Cursor, Claude Code, and Codex CLI so each client has an explicit “with Web UI” variant. Examples must be copy/paste-ready, consistent with actual wrapper CLI options, and aligned with current configuration formats used in this repository (`json` snippets for Zed/Cursor and command-line examples for Claude/Codex).

The deliverable is documentation/config updates only; runtime behavior is already implemented and out of scope for code changes.

## Success Criteria and Acceptance Tests
- Each target client has a concrete Web UI-enabled example that includes both `--web-ui` and `--web-ui-port`.
- No existing non-Web-UI examples are removed; Web UI usage is additive and clearly labeled optional.
- Examples are syntactically valid for each client’s expected format.
- README and docs remain internally consistent (same flags, same option spelling, no contradictory guidance).

Acceptance tests:
1. Search-based verification confirms all four clients expose Web UI example usage.
2. Manual snippet review confirms command argument placement is correct per client format.
3. `pytest`, `ruff check src/`, `mypy src/`, and `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` all pass.

## Test-First Plan
1. Add/adjust docs assertions through deterministic checks:
   - `rg` checks for each client and each flag (`--web-ui`, `--web-ui-port`).
2. Make minimal doc/config edits needed to satisfy checks.
3. Re-run search checks and standard quality gates.

## Hierarchical TODO Plan
### Phase A — Baseline and Scope Validation
- **Inputs:** `README.md`, `docs/*setup.md`, `config/*` examples.
- **Outputs:** Gap list showing where Web UI argument examples are missing.
- **Verification:** `rg` output demonstrates pre-change absence or incompleteness.

### Phase B — Implement Documentation and Config Updates
- **Inputs:** Gap list from Phase A.
- **Outputs:** Updated snippets for Zed, Cursor, Claude Code, and Codex CLI showing Web UI variants.
- **Verification:** Render/read each snippet for correctness and consistency of flag usage.

### Phase C — Validate and Record Evidence
- **Inputs:** Updated files.
- **Outputs:** Passing quality gates and a validation report at `SPECS/INPROGRESS/FU-REBUILD-P10-T1-4_Validation_Report.md`.
- **Verification:** Command outputs captured in report with PASS/PARTIAL/FAIL verdict.

## Decision Points and Constraints
- Keep defaults unchanged: Web UI remains optional and opt-in.
- Use a single illustrative port (8080) unless an existing file already uses another standard.
- Avoid introducing client-specific behavior claims not backed by existing project behavior.

## Notes
After implementation, ensure these references remain aligned:
- `README.md` client sections
- `docs/cursor-setup.md`, `docs/claude-setup.md`, `docs/codex-setup.md`
- `config/cursor-mcp.json`, `config/claude-code.txt`, `config/codex-cli.txt`, `config/zed-agent.json`

---
**Archived:** 2026-02-11
**Verdict:** PASS
