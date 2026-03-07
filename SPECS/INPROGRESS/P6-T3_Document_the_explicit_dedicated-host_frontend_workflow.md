# P6-T3 — Document the explicit dedicated-host frontend workflow

## Objective Summary

Phase 6 now has the runtime status API (`P6-T1`) and a standalone terminal
frontend (`P6-T2`), but the operator docs still present the explicit
dedicated-host pattern mostly as an alternative rather than the clearest path
for users who want predictable lifecycle and visibility. This task updates the
user-facing documentation so multi-editor users can adopt one shared
broker-daemon plus one monitoring frontend without reverse-engineering which
process owns the dashboard, how to verify a shared daemon, or where `--tui`
fits compared with browser-based monitoring.

The docs should make a simple decision tree obvious:
- use unified auto-spawn when convenience matters more than operator control
- use one explicit dedicated host when you want stable lifecycle and one place
  to inspect broker health
- use the browser dashboard and/or `--tui` as complementary frontend surfaces
  for that dedicated host

## Deliverables

- Update `README.md` to recommend the explicit dedicated-host + frontend
  workflow for users who want strong visibility into broker health across
  multiple editors/clients.
- Update `docs/broker-mode.md` so the dedicated-host pattern includes explicit
  start, frontend attach, and verification steps for proving that multiple
  editors share one daemon.
- Update related operator docs (`docs/webui-setup.md`,
  `docs/troubleshooting.md`, and any necessary client/setup pages) so frontend
  ownership, `--tui`, and dedicated-host verification guidance are consistent.
- If needed for clarity, add one focused user-facing guide under `docs/` that
  explains the explicit frontend workflow end-to-end.

## Success Criteria

- README explains when to prefer a dedicated broker host with an explicit
  monitoring frontend over implicit auto-spawn.
- Broker docs describe how to confirm two editors or MCP clients are attached
  to one shared daemon using concrete checks (`--broker-status`, PID/socket,
  log/TUI/dashboard state, etc.).
- Frontend launch steps for both browser dashboard and terminal UI are
  documented in a user-facing guide or equivalent focused sections.
- Troubleshooting guidance clearly distinguishes “multiple broker rows in
  Xcode” from “multiple live daemons” and points users to the dedicated-host
  verification flow.

## Test-First Plan

1. Audit the current operator docs to identify where dedicated host, Web UI
   ownership, and `--tui` are already mentioned and where the guidance is still
   fragmented.
2. Draft the dedicated-host workflow in one place first so the terminology,
   commands, and verification steps are fixed before updating cross-links.
3. Update README and the main broker/Web UI/troubleshooting docs to reference
   that same workflow and avoid contradictory recommendations.
4. Run the documentation quality gates and a focused doc-sync check after the
   content is updated.

## Execution Plan

### Phase 1: Documentation topology and messaging

Inputs:
- `README.md`
- `docs/broker-mode.md`
- `docs/webui-setup.md`
- `docs/troubleshooting.md`
- current Phase 6 runtime behavior from `P6-T1` and `P6-T2`

Outputs:
- one consistent story for auto-spawn vs dedicated host
- one chosen review subject name for this docs slice

Verification:
- docs no longer describe the dedicated-host frontend workflow as a vague
  alternative with missing verification steps

### Phase 2: Dedicated-host workflow documentation

Inputs:
- broker host commands and status commands
- browser dashboard and `--tui` launch/usage model
- multi-editor verification needs from user feedback

Outputs:
- dedicated-host startup and verification steps
- explicit frontend monitoring/control guidance
- examples that show both editors attach to one daemon while one frontend
  monitors it

Verification:
- a user can follow the docs end-to-end without inferring missing lifecycle
  steps

### Phase 3: Cross-links, consistency, and validation

Inputs:
- updated docs content
- existing README/docs cross-link structure

Outputs:
- aligned cross-references between README, broker docs, Web UI docs, and
  troubleshooting
- validation report with required gate results

Verification:
- terminology and commands are consistent across all touched docs
- quality gates remain green

## Acceptance Tests

- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`
- `python tests/test_check_doc_sync.py --mode branch`

## Decision Points

- Prefer strengthening existing core docs before adding a brand-new guide, but
  create a focused workflow page if that materially improves user navigation.
- Treat `--tui` and the browser dashboard as complementary frontends for one
  explicit host, not competing deployment modes.
- Use exact commands and exact file paths (`~/.mcpbridge_wrapper/*`) in the
  docs so users can verify the shared-daemon topology concretely.

## Notes

- Keep client-specific setup pages lightweight unless they need a direct link
  or short note pointing into the dedicated-host workflow.
- Do not introduce new product promises beyond current behavior; document what
  Phase 6 already shipped.
- Review subject name for this task: `dedicated_host_frontend_docs`.
