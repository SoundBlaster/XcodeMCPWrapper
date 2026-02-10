# Review: REBUILD-P10-T1 Web UI Rebuild Package

**Review Date:** 2026-02-10  
**Task:** REBUILD-P10-T1  
**Reviewer:** Codex  
**Overall Assessment:** PASS with follow-up recommendations

## Findings

1. **[P2] WebSocket auth path likely inconsistent with frontend behavior**
   - Evidence: `src/mcpbridge_wrapper/webui/server.py` expects a `token` query param for `/ws/metrics` when auth is enabled; `src/mcpbridge_wrapper/webui/static/dashboard.js` currently creates WebSocket URL without token.
   - Impact: Auth-enabled dashboards may fall back to polling and lose realtime stream guarantees.

2. **[P2] CLI arg validation for `--web-ui-port` is not hardened**
   - Evidence: `src/mcpbridge_wrapper/__main__.py` casts user values via `int(...)` without explicit guard.
   - Impact: malformed input can terminate startup with uncaught `ValueError` semantics.

3. **[P2] Documentation/runtime env-var mismatch**
   - Evidence: `docs/webui-setup.md` references `MCP_WRAPPER_WEB_UI*`; runtime reads `WEBUI_*` and CLI flags.
   - Impact: operators may believe env toggle is supported when it is not.

## Strengths

- REBUILD Step 0-7 outputs are complete and schema-valid.
- Final package includes required files and required heading structures.
- Quality gates pass (`pytest`, `ruff`, `mypy`, `pytest --cov`) with coverage above threshold.

## Verdict

PASS - Artifact package is complete and usable for implementation kickoff. Follow-up tasks are recommended for runtime hardening and operator clarity.
