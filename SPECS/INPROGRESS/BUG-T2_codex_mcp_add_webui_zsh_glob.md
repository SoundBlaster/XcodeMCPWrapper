# BUG-T2 PRD — codex mcp add with Web UI extras fails in zsh

## 1. Context

When users run Codex MCP setup with uvx extras using an unquoted package specifier, zsh treats `[...]` as a glob pattern and fails before executing `uvx`.

Failing command observed:

```zsh
codex mcp add xcode -- uvx --from mcpbridge-wrapper[webui] mcpbridge-wrapper --web-ui --web-ui-port 8080
# zsh: no matches found: mcpbridge-wrapper[webui]
```

## 2. Goal

Make all user-facing shell command examples for uvx Web UI extras shell-safe in zsh and add explicit troubleshooting guidance.

## 3. Scope

In scope:
- Documentation and setup snippets where users copy/paste shell commands
- Troubleshooting updates for `zsh: no matches found`
- Task tracking updates for BUG-T2 completion

Out of scope:
- Runtime code changes in wrapper core
- MCP protocol behavior changes

## 4. Deliverables

- Updated docs and command snippets to use quoted extras form:
  - `uvx --from 'mcpbridge-wrapper[webui]' ...`
- Troubleshooting section with symptom/cause/fix for zsh globbing
- Validation report at `SPECS/INPROGRESS/BUG-T2_Validation_Report.md`

## 5. Acceptance Criteria

1. No unquoted shell command examples remain for `uvx --from mcpbridge-wrapper[webui]` in active docs/config text examples.
2. Codex setup examples with Web UI extras show a zsh-safe command form.
3. Troubleshooting docs include the exact symptom `zsh: no matches found: mcpbridge-wrapper[webui]` and a fix.
4. Quality gates pass:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov` with project coverage >= 90%

## 6. Dependencies

- Existing bug record in `SPECS/Workplan.md` (`BUG-T2`)
- Existing docs pages: README, codex setup, troubleshooting, AGENTS

## 7. Implementation Plan

1. Find all user-facing shell examples using unquoted extras.
2. Update command snippets to quoted extras.
3. Add troubleshooting guidance for zsh glob expansion.
4. Run quality gates and capture results.
5. Archive task artifacts according to FLOW.

## 8. Risks and Mitigations

- Risk: Over-editing machine-readable config examples where shell quoting is irrelevant.
- Mitigation: Restrict quoting changes to shell command strings and explanatory text meant for terminal copy/paste.
