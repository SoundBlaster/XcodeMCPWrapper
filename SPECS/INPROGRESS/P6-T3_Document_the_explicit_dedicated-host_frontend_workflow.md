# P6-T3 — Document the explicit dedicated-host frontend workflow

## Objective Summary

`P6-T1` and `P6-T2` added the runtime status API and a standalone TUI, but the
operator docs still present unified auto-spawn as the default multi-editor
story. This task updates the user-facing guidance so the recommended workflow
for users who want explicit visibility and lower confusion is: start one
dedicated broker host, expose one shared monitoring surface, and point every
editor at that host with `--broker`.

The docs must make two things unambiguous. First, when dedicated host mode is
preferable to implicit auto-spawn: multi-editor setups, first-approval
debugging, reconnect storms, and any situation where the user wants one place
to see daemon health. Second, how the frontend fits into that topology: the
browser dashboard is hosted by the broker host, and `--tui` is a terminal
frontend that attaches to that existing dashboard/status surface rather than
starting its own broker.

## Deliverables

- Update `README.md` so multi-editor guidance recommends one dedicated
  `--broker-daemon --web-ui` host plus one explicit monitoring frontend.
- Update `docs/broker-mode.md` with a concrete dedicated-host workflow,
  verification steps for “both editors share one daemon”, and TUI usage.
- Update `docs/webui-setup.md` and `docs/troubleshooting.md` so frontend
  ownership, dedicated-host diagnostics, and TUI expectations are coherent.
- Add short dedicated-host pointers in `docs/cursor-setup.md`,
  `docs/claude-setup.md`, and `docs/codex-setup.md`.
- Keep mapped DocC mirrors in sync for every changed docs/ file:
  `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`,
  `WebUIDashboard.md`, `Troubleshooting.md`, `CursorSetup.md`,
  `ClaudeCodeSetup.md`, and `CodexCLISetup.md`.

## Success Criteria

- README explains when to prefer an explicit dedicated host over implicit
  auto-spawn and links users to the broker/frontend workflow.
- Broker docs show how to start one host, connect multiple editors with
  `--broker`, and verify that they are sharing one daemon.
- Frontend docs explain the relationship between broker-hosted Web UI and
  `--tui`, including how to launch the TUI against an existing dashboard.
- Troubleshooting covers concrete checks for “one daemon, many editors” and
  “frontend unavailable even though broker is alive”.
- `docs/` changes pass DocC sync checks with same-commit pairing.

## Test-First Plan

1. Identify the exact sections whose current wording still presents unified
   auto-spawn as the preferred multi-editor path.
2. Decide the canonical operator recipe and command snippets before editing:
   one broker host, one dashboard endpoint, optional TUI attachment, all
   editors on `--broker`.
3. Update the mapped markdown + DocC pairs in the same logical commit so
   `doccheck-all-strict` can pass without cleanup commits.
4. Run required quality gates from FLOW plus doc sync validation:
   `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov`,
   `make doccheck-all-strict`.
5. Re-read the changed docs as a user journey to ensure the workflow is
   consistent across README, setup guides, broker guide, and troubleshooting.

## Execution Plan

### Phase 1: Canonical workflow definition

Inputs:
- `README.md`
- `docs/broker-mode.md`
- `docs/webui-setup.md`
- `docs/troubleshooting.md`

Outputs:
- one canonical dedicated-host narrative
- exact commands for host start, client config, frontend launch, and verification
- explicit statement of when auto-spawn remains acceptable

Verification:
- the same recommended workflow appears consistently across top-level docs
- terminology distinguishes daemon host, client proxy, dashboard, and TUI

### Phase 2: User-facing guide updates

Inputs:
- canonical workflow from Phase 1
- current client setup guides

Outputs:
- refreshed README multi-editor guidance
- broker-mode guide sections for dedicated-host workflow, shared-daemon checks,
  and TUI usage
- concise dedicated-host pointers in Cursor / Claude Code / Codex setup guides

Verification:
- a user can start from a client-specific setup page and find the explicit host
  workflow without reading the entire repo
- commands are copy-pasteable and use current flags only

### Phase 3: Troubleshooting and DocC sync

Inputs:
- updated docs pages
- `scripts/check_doc_sync.py` mapping

Outputs:
- troubleshooting steps for verifying one daemon and one frontend owner
- synced DocC mirror files for every mapped docs/ change
- validation report with FLOW quality gates + doc sync results

Verification:
- `make doccheck-all-strict` passes
- troubleshooting points to the dedicated-host frontend workflow as the most
  explicit recovery path for confusing multi-editor states

## Acceptance Tests

- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`
- `make doccheck-all-strict`

## Decision Points

- The docs should recommend dedicated host mode specifically for explicit
  observability and multi-editor predictability, not for every broker user.
- The TUI should be documented as a frontend to the broker-hosted dashboard/API,
  not as an alternative daemon mode.
- Client-specific setup docs should stay short and defer deep lifecycle detail
  to `docs/broker-mode.md`, but they still need one clear pointer to the
  dedicated-host workflow.

## Notes

- `docs/broker-mode.md` currently has no DocC-mapped mirror, so the broker
  guide itself must remain self-contained and authoritative for the explicit
  host workflow.
- Keep examples aligned with modern `mcpbridge-wrapper` command names rather
  than legacy `xcodemcpwrapper` usage except where historical compatibility is
  already documented.
- Review subject name for this task: `dedicated_host_frontend_docs`.
