# Workplan: mcpbridge-wrapper

## Archived Baseline

The previous workplan for release `0.4.0` was archived at:

- [Workplan_0.4.0.md](ARCHIVE/_Historical/Workplan_0.4.0.md)

## Current Cycle

This file is intentionally reset for the next planning cycle.
Add new tasks using the canonical template in [TASK_TEMPLATE.md](TASK_TEMPLATE.md).

## Tasks

### Phase 1: Documentation

#### ✅ P1-T1: Add the version badge in the README.md
- **Status:** ✅ Completed (2026-02-28)
- **Description:** Add a package version badge to `README.md` so users can quickly see the currently published version.
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` badge section updated with a version badge
  - Badge target URL configured to an authoritative version source
- **Acceptance Criteria:**
  - [x] `README.md` includes a visible version badge near the project heading or badges area
  - [x] The badge renders correctly and links to the canonical published version page

#### ✅ P1-T2: Add Xcode 26.4 known issue release-notes link to README
- **Status:** ✅ Completed (2026-02-28)
- **Description:** Update `README.md` to include a link to the official Xcode 26.4 release notes for the Coding Intelligence known issue: "When using external development tools that connect to Xcode, you may see multiple \"Allow Connection?\" dialogs during normal usage. (170721057)".
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` updated with the official Xcode release-notes reference link
  - A note in `README.md` that points users to the documented known issue (170721057)
- **Acceptance Criteria:**
  - [x] `README.md` includes a link to `https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes`
  - [x] `README.md` mentions the Coding Intelligence known issue about repeated "Allow Connection?" dialogs and references issue ID `170721057`

#### ✅ P1-T3: Improve MCP settings examples in README to present broker setup first
- **Status:** ✅ Completed (2026-03-01)
- **Description:** Update `README.md` MCP configuration examples for different agents so broker-based setup appears first, making the recommended integration path clear and consistent.
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` MCP settings examples reordered/updated to show broker setup first for each supported agent
  - Example snippets validated for clarity and consistency across agent sections
- **Acceptance Criteria:**
  - [x] `README.md` presents broker setup before alternative/manual setup in MCP settings examples for Cursor, Claude Code, and Codex CLI
  - [x] The MCP example sections use consistent wording and ordering so users can follow the broker-first path without ambiguity

#### ✅ P1-T4: Update docs to reflect broker robustness improvements (P2-T1 – P2-T5)
- **Status:** ✅ Completed (2026-03-01)
- **Description:** The docs/broker-mode.md, docs/troubleshooting.md, docs/cursor-setup.md, docs/claude-setup.md, and docs/codex-setup.md (plus their DocC mirrors) still reference the old `--broker-spawn`/`--broker-connect` flags as primary options, describe stale-socket cleanup as manual, and omit the new `--broker` flag (P2-T1), auto-recovery behaviour (P2-T2), JSON-RPC -32001 error response (P2-T4), and the web-UI mismatch warning (P2-T5). Update all five docs + four DocC files to reflect the current behaviour.
- **Priority:** P2
- **Dependencies:** P2-T1, P2-T2, P2-T4, P2-T5
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `docs/broker-mode.md` — mode table, topology, examples, limitations updated
  - `docs/troubleshooting.md` — stale-recovery, connect-timeout, web-UI mismatch entries updated
  - `docs/cursor-setup.md`, `docs/claude-setup.md`, `docs/codex-setup.md` — broker examples updated
  - `Sources/XcodeMCPWrapper/Documentation.docc/` — four mirror files synced
- **Acceptance Criteria:**
  - [ ] `--broker` appears as the recommended flag in all broker sections
  - [ ] `--broker-connect`/`--broker-spawn` demoted to legacy/advanced entries
  - [ ] Stale-socket recovery described as automatic for `--broker`/`--broker-spawn`
  - [ ] Troubleshooting entry for JSON-RPC -32001 error present
  - [ ] New troubleshooting entry for "Warning: broker is running without --web-ui" present
  - [ ] DocC sync check passes (`make doccheck-all`)

#### ✅ P1-T5: Fix missed --broker-spawn references in troubleshooting.md "MCP tools are green" section
- **Status:** ✅ Completed (2026-03-04)
- **Description:** Verified and archived this follow-up as already satisfied on the latest `main` baseline: both targeted lines in `docs/troubleshooting.md` already use `--broker --web-ui`, matching the DocC mirror and eliminating the previously reported mismatch.
- **Priority:** P2
- **Dependencies:** P1-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `SPECS/ARCHIVE/P1-T5_Fix_missed_broker_spawn_references_in_troubleshooting/` — archived PRD + validation report
  - `SPECS/ARCHIVE/P1-T5_Fix_missed_broker_spawn_references_in_troubleshooting/P1-T5_Validation_Report.md` — verification evidence for no-op completion
- **Acceptance Criteria:**
  - [x] `docs/troubleshooting.md` line "only starts one when it must spawn a host" uses `--broker --web-ui`
  - [x] `docs/troubleshooting.md` "Unified broker single-config" solution option uses `--broker --web-ui`
  - [x] `make doccheck-all` passes (mirrors stay in sync)

#### ✅ P1-T6: Update webui-setup.md and DocC mirror to use --broker in multi-agent examples
- **Status:** ✅ Completed (2026-03-04)
- **Description:** Verified and archived this follow-up as already satisfied on the latest `main` baseline: both `docs/webui-setup.md` and `Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md` already use `--broker` in the targeted multi-agent examples and remain in sync.
- **Priority:** P3
- **Dependencies:** P1-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `SPECS/ARCHIVE/P1-T6_Update_webui_setup_and_DocC_mirror_to_use_broker_in_multi_agent_examples/` — archived PRD + validation report
  - `SPECS/ARCHIVE/P1-T6_Update_webui_setup_and_DocC_mirror_to_use_broker_in_multi_agent_examples/P1-T6_Validation_Report.md` — verification evidence for no-op completion
- **Acceptance Criteria:**
  - [x] `docs/webui-setup.md` multi-agent broker example uses `--broker`
  - [x] DocC mirror updated to match
  - [x] `make doccheck-all` passes

#### ✅ P1-T7: Hide README version badge maintenance note
- **Status:** ✅ Completed (2026-03-01)
- **Description:** Hid from `README.md` the string `Version badge maintenance: run make badge-version (or make badge-version-check in CI).` while preserving the visible version badge.
- **Priority:** P3
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` — maintenance note string removed from badge area
- **Acceptance Criteria:**
  - [x] `README.md` no longer contains the exact string `Version badge maintenance: run make badge-version (or make badge-version-check in CI).`
  - [x] Version badge remains visible and functional after removing the maintenance note

#### ✅ P1-T8: Update /config examples for broker setup first
- **Status:** ✅ Completed (2026-03-01)
- **Description:** Update MCP client templates under `config/` so broker-mode setup is presented first and consistently framed as the recommended path.
- **Priority:** P1
- **Dependencies:** P2-T6
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `config/cursor-mcp.json` and `config/zed-agent.json` reordered to show broker-mode options before non-broker alternatives
  - `config/claude-code.txt` and `config/codex-cli.txt` updated so broker commands appear before non-broker commands
- **Acceptance Criteria:**
  - [x] Cursor and Zed config templates present a broker-mode option first
  - [x] Claude Code and Codex CLI config templates present a broker command first
  - [x] Broker-first guidance is consistent with existing `*-broker` templates and `--broker` usage

#### ✅ P1-T10: Document Xcode first-approval timing race in Troubleshooting & Known Issues
- **Status:** ✅ Completed (2026-03-06)
- **Description:** When broker mode is used for the first time, Xcode shows an approval dialog for the new daemon process. If an MCP client (Zed, Cursor) connects and sends `tools/list` before Xcode grants approval, it receives an empty tools list and caches it — showing 0 tools indefinitely until the user manually reloads the MCP connection. This is a real usability trap: the green dot shows "connected" but 0 tools, with no clear error. Document the root cause, the correct first-time setup sequence, and the recovery steps in `docs/troubleshooting.md` and as a Known Issue in `README.md`. Also note that each unique process identity (direct wrapper vs broker daemon) triggers a separate Xcode dialog.
- **Priority:** P1
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `docs/troubleshooting.md` — new section "MCP client shows 0 tools (green dot) after first broker connection"
  - `README.md` — Known Issues entry expanded for first-approval race condition
  - DocC mirror synced (`Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`)
- **Acceptance Criteria:**
  - [x] `docs/troubleshooting.md` describes the symptom (green dot, 0 tools), root cause (Xcode dialog timing race), correct setup sequence (start broker first → approve → then connect clients), and recovery steps (reload MCP in client after approval)
  - [x] `docs/troubleshooting.md` notes that each new process identity (direct vs broker daemon) triggers a separate Xcode dialog
  - [x] `README.md` Known Issues section includes this scenario
  - [x] DocC Troubleshooting.md mirrors the new section

#### ✅ P1-T9: Add direct links for all command steps in FLOW.md
- **Status:** ✅ Completed (2026-03-03)
- **Description:** `SPECS/COMMANDS/FLOW.md` now includes direct links for command-backed steps in both the step sections and quick-reference coverage, including a direct PLAN link.
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `SPECS/COMMANDS/FLOW.md` updated with direct links for command-backed workflow steps
  - `SPECS/ARCHIVE/P1-T9_Add_direct_links_for_all_command_steps_in_FLOW/` archived task artifacts
- **Acceptance Criteria:**
  - [x] `SPECS/COMMANDS/FLOW.md` includes direct links for command-backed steps, including PLAN (`PLAN.md`)
  - [x] Any summary or quick-reference text in `SPECS/COMMANDS/FLOW.md` remains consistent with the linked-step wording
  - [x] All links resolve correctly within `SPECS/COMMANDS/`

#### ✅ P1-T11: Update test coverage badge in README.md with actual numbers
- **Status:** ✅ Completed (2026-03-06)
- **Description:** The README coverage badge and performance summary currently show a hard-coded coverage percentage. Recompute the current project coverage from the test suite and update the README so the displayed coverage numbers match the measured result.
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` coverage badge updated to the current measured coverage percentage
  - `README.md` Performance section coverage metric kept in sync with the same validated value
- **Acceptance Criteria:**
  - [x] `README.md` coverage badge value matches the coverage percentage recorded in the task validation report
  - [x] `README.md` Performance section coverage value matches the badge and the same validation result

#### ✅ P1-T12: Improve troubleshooting docs for Zed broker startup timeouts
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Extended the broker troubleshooting guidance with the Zed-specific first-approval failure pattern where Zed can briefly show 0 tools and then fail with `Context server request timeout`. The docs now capture the dedicated-host recovery sequence and explain how to interpret inactive `mcpbridge-broker` rows in Xcode Agent Activity.
- **Priority:** P1
- **Dependencies:** P1-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `docs/troubleshooting.md` updated with a Zed-specific timeout recovery subsection
  - `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` synced with the same Zed guidance
  - `SPECS/ARCHIVE/P1-T12_Improve_troubleshooting_docs_for_Zed_broker_startup_timeouts/` archived task artifacts
- **Acceptance Criteria:**
  - [x] `docs/troubleshooting.md` documents the Zed sequence of green/0 tools after approval followed by `Context server request timeout` on restart
  - [x] `docs/troubleshooting.md` includes a step-by-step dedicated-host recovery flow using `mcpbridge-wrapper --broker-stop` and manual `--broker-daemon` startup
  - [x] `docs/troubleshooting.md` explains that inactive `mcpbridge-broker` entries in Xcode Agent Activity are usually historical sessions, not proof of multiple live brokers
  - [x] `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` mirrors the new guidance

#### ✅ P1-T13: Document stale editable install version mismatch in troubleshooting guide
- **Status:** ✅ Completed (2026-03-10)
- **Description:** When developing locally, the `.venv` editable install records the package version at install time in its `dist-info` directory. If `pyproject.toml` is bumped to a new version without re-running `pip install -e .`, the `mcpbridge-wrapper` command in the dev PATH still reports the old version. This causes `--doctor` to show a version mismatch between the running broker (started via `uvx`, which fetches the latest from PyPI) and the local binary. Document this scenario, its cause, and the fix (`pip install -e .` or `.venv/bin/pip install -e .`) in `docs/troubleshooting.md` so developers can self-diagnose without manual inspection of dist-info directories.
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `docs/troubleshooting.md` — new entry under a "Development / Editable Install" section explaining the stale dist-info version mismatch and the fix
  - `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` — DocC mirror synced
  - `SPECS/ARCHIVE/P1-T13_Document_stale_editable_install_version_mismatch_in_troubleshooting_guide/` — archived PRD and validation report
- **Acceptance Criteria:**
  - [x] `docs/troubleshooting.md` describes the symptom (`--doctor` reports version mismatch, package version is old), the root cause (stale editable dist-info after `pyproject.toml` bump), and the fix (`pip install -e .`)
  - [x] The entry clarifies that `uvx` always fetches the latest PyPI release while the `.venv` editable install reflects the version at the time of `pip install -e .`
  - [x] DocC mirror (`Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`) is updated to match
  - [x] `make doccheck-all` passes

### Phase 2: Broker Robustness

#### ✅ P2-T1: Replace --broker-spawn/--broker-connect with single --broker flag
- **Status:** ✅ Completed (2026-03-01)
- **Description:** Users currently must choose between `--broker-spawn` (auto-start daemon if absent) and `--broker-connect` (require daemon already running). This distinction is invisible to users — they just want broker mode. Introduce a single `--broker` flag that auto-detects: connect if daemon is alive, spawn otherwise. Keep `--broker-spawn` and `--broker-connect` as hidden aliases for backwards compatibility. Update all documentation and MCP settings examples to use `--broker`.
- **Priority:** P1
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/__main__.py` — `--broker` flag added, auto-detect logic
  - README updated to use `--broker` in all MCP settings examples
- **Acceptance Criteria:**
  - [x] `--broker` flag auto-connects when daemon is alive, spawns when absent
  - [x] `--broker-spawn` and `--broker-connect` still work unchanged
  - [x] All MCP settings examples in README use `--broker`
  - [x] All existing tests pass

#### ✅ P2-T2: Self-healing stale socket and PID file recovery
- **Status:** ✅ Completed (2026-03-01)
- **Description:** When the broker daemon crashes or is killed, it leaves `broker.sock` and `broker.pid` on disk. The proxy's `_spawn_broker_if_needed` checks `socket_path.exists()` and skips spawning if the socket file is present — even if no process is listening. This silently blocks all future broker mode sessions until the user manually deletes the files. Fix by validating socket liveness via `connect()` before concluding a broker is running: if `connect()` fails with `ConnectionRefusedError`, treat both files as stale, remove them, and proceed with spawn. Also clean up socket file on daemon exit via `atexit`/signal handler.
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/proxy.py` — liveness check in `_spawn_broker_if_needed`
  - `src/mcpbridge_wrapper/broker/daemon.py` — socket cleanup on exit
- **Acceptance Criteria:**
  - [x] After broker crash, next `--broker-spawn` (or `--broker`) session auto-recovers without manual file removal
  - [x] Liveness check uses `connect()` not `exists()`
  - [x] Daemon removes `broker.sock` on clean exit and on SIGTERM
  - [x] All existing broker tests pass

#### ✅ P2-T3: Fix double-spawn race condition when MCP client toggles rapidly
- **Status:** ✅ Completed (2026-03-01)
- **Description:** When an MCP client (e.g. Zed) toggles the connection off/on quickly, two proxy processes start simultaneously. Both check for a running broker, find none, and both spawn a daemon. Two competing daemons fight over the socket path: one wins, the other crashes. The losing proxy's client gets no broker and shows 0 tools. Fix with a filesystem lock (e.g. `fcntl.flock` on the PID file) so only one spawn attempt proceeds at a time; the second waiter detects the winner's daemon and connects.
- **Priority:** P1
- **Dependencies:** P2-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/proxy.py` — spawn lock in `_spawn_broker_if_needed`
- **Acceptance Criteria:**
  - [x] Rapid double-toggle produces exactly one broker daemon, both proxy sessions connect successfully
  - [x] Lock is released on proxy exit (including crash)
  - [x] All existing broker tests pass

#### ✅ P2-T4: Surface broker unavailability as JSON-RPC error instead of silent timeout
- **Status:** ✅ Completed (2026-03-01)
- **Description:** When the proxy cannot connect to the broker (stale socket, spawn failed, daemon crashed mid-session), the client receives no response and eventually times out — showing "0 tools" or a generic connection error with no actionable message. Instead, the proxy should return a JSON-RPC error response (e.g. code `-32001`, message `"Broker unavailable: <reason>"`) so MCP clients can surface a meaningful error to the user rather than silently hanging.
- **Priority:** P1
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/proxy.py` — `_send_broker_error()` helper; connect phase wrapped in try/except
- **Acceptance Criteria:**
  - [x] Connection timeout produces a JSON-RPC `-32001` error response to the client
  - [x] Error message includes a human-readable reason (timeout, refused, stale socket)
  - [x] Client does not hang indefinitely — error is returned within `connect_timeout` seconds

#### ✅ P2-T5: Warn or restart daemon when --web-ui requested but running broker lacks it
- **Status:** ✅ Completed (2026-03-01)
- **Description:** When a user configures `--broker-spawn --web-ui` and a broker daemon is already running without the web UI, the proxy connects silently and the `--web-ui` flag has no effect. The user sees 0 web UI and no explanation. Fix by detecting the mismatch: if the proxy is asked for web UI but the running daemon does not expose a web UI port (detectable via a broker status endpoint or absence of HTTP response on the expected port), emit a clear warning to stderr: `"Warning: broker is running without --web-ui. Restart the broker to enable the dashboard."`.
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/proxy.py` — `_warn_web_ui_mismatch()` helper; `web_ui_port` param; `_new_broker_spawned` flag
  - `src/mcpbridge_wrapper/__main__.py` — passes effective web UI port to `BrokerProxy`
- **Acceptance Criteria:**
  - [x] When `--web-ui` is passed to proxy but running broker has no web UI, a warning is printed to stderr
  - [x] Warning text is actionable (tells user how to fix it)
  - [x] MCP session continues normally despite the warning

#### ✅ P2-T6: Remove legacy --broker-connect and --broker-spawn flags
- **Status:** ✅ Completed (2026-03-01)
- **Description:** Broker mode aliases `--broker-connect` and `--broker-spawn` were kept only for backwards compatibility. Broker mode has not shipped yet, so compatibility is unnecessary and the aliases now add confusion to docs and tests. Remove both legacy flags from wrapper CLI parsing and documentation, and keep `--broker` as the single proxy-mode entrypoint (plus `--broker-daemon` for host mode).
- **Priority:** P1
- **Dependencies:** P2-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/__main__.py` — remove legacy broker alias parsing/comments
  - `tests/unit/test_main.py`, `tests/unit/test_broker_proxy.py` — remove/update alias-specific tests
  - `README.md` and `docs/*.md` — remove alias guidance/examples and align to `--broker`
- **Acceptance Criteria:**
  - [x] Wrapper no longer accepts `--broker-connect` and `--broker-spawn` as broker control flags
  - [x] Documentation no longer presents legacy alias usage or compatibility notes
  - [x] Broker mode guidance remains clear with `--broker` (proxy) and `--broker-daemon` (host)
  - [x] Required quality gates pass (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` with coverage >=90%)

#### ✅ P2-T8: Gate broker tools/list on warmed tool catalog
- **Status:** ✅ Completed (2026-03-10)
- **Description:** Cursor and Zed can cache the first successful `tools/list` response they receive from `mcpbridge-wrapper`. Today the broker releases client `tools/list` requests immediately after upstream `initialize`, even if the broker has not yet completed its own `notifications/initialized` + `tools/list` warm-up and populated a stable tool cache. During cold-start or Xcode approval timing, that lets strict clients see an empty or invalid tool list and forces users to toggle the server several times before all 20 Xcode tools appear. Fix the broker so external `tools/list` waits for a warmed non-empty catalog instead of racing the warm-up path.
- **Priority:** P0
- **Dependencies:** BUG-T9, P4-T2
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/daemon.py` — explicit tool-catalog readiness gate and empty-catalog handling
  - `src/mcpbridge_wrapper/broker/transport.py` — hold client `tools/list` until broker cache is ready
  - `tests/unit/test_broker_daemon.py`, `tests/unit/test_broker_transport.py` — broker warm-up regression coverage
  - `tests/integration/test_broker_multi_client.py` — integration coverage updated for the new broker contract
- **Acceptance Criteria:**
  - [x] Broker does not forward client `tools/list` while its internal tool catalog is still cold
  - [x] Empty or invalid broker `tools/list` probe results do not open the client-facing readiness gate
  - [x] Cursor/Zed-style first `tools/list` requests receive either a warmed catalog or a clear TTL error, never a prematurely cached empty success
  - [x] Required quality gates pass (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` with coverage >=90%)

### Phase 3: Web UI Controls

#### ✅ P3-T11: Add Stop broker/service control button to Web UI
- **Status:** ✅ Completed (2026-03-01)
- **Description:** Add a Web UI control that lets users request graceful shutdown of the running broker/service process directly from the dashboard, with clear availability rules and safe behavior in unsupported modes.
- **Priority:** P1
- **Dependencies:** P2-T6
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/webui/server.py` — control capability + stop endpoint
  - `src/mcpbridge_wrapper/webui/static/index.html` — Stop control button
  - `src/mcpbridge_wrapper/webui/static/dashboard.js` — control discovery + stop action handler
  - `src/mcpbridge_wrapper/__main__.py` — broker-daemon shutdown wiring for Web UI control
  - `tests/unit/webui/test_server.py` — endpoint and capability tests
- **Acceptance Criteria:**
  - [x] Dashboard exposes a Stop control only when backend reports stop capability
  - [x] `POST /api/control/stop` returns accepted and triggers graceful broker shutdown in broker-daemon mode
  - [x] Unsupported runtime modes return a clear non-2xx response for stop requests
  - [x] Unit tests cover both supported and unsupported stop-control paths

### Bug Fixes

#### ✅ BUG-T9: Fix broker daemon not sending notifications/initialized before tools/list probe
- **Status:** ✅ Completed (2026-03-06)
- **Description:** After the broker's own `initialize` probe succeeds, it immediately sends a `tools/list` probe without first sending the `notifications/initialized` notification. xcrun mcpbridge requires this notification to complete the MCP handshake before it responds to any subsequent requests, so it queues `tools/list` indefinitely. `_read_upstream_loop` blocks forever on `readline()` waiting for the tools/list response; all client requests forwarded to upstream never get responses; every client socket times out. Fixed by sending `notifications/initialized` after the init probe ack and before the `tools/list` probe.
- **Priority:** P0
- **Dependencies:** P4-T2
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/daemon.py` — send `notifications/initialized` before `tools/list` probe
  - `tests/unit/test_broker_daemon.py` — assert notification is sent before probe with correct ordering
- **Acceptance Criteria:**
  - [x] `notifications/initialized` notification is written to upstream stdin immediately after the init probe ack
  - [x] `notifications/initialized` appears before the `tools/list` probe in the written message sequence
  - [x] `tools/list` probe response is received and cached after the fix
  - [x] Client `initialize` → `tools/list` round-trip succeeds end-to-end via the broker socket
  - [x] All 785 tests pass with no regressions

#### ✅ BUG-T8: Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper
- **Status:** ✅ Completed (2026-03-01)
- **Description:** `BrokerProxy._make_stdout_writer` wraps `sys.stdout.buffer` using `asyncio.BaseProtocol` as the protocol, but `asyncio.StreamWriter.drain()` calls `protocol._drain_helper()` which `BaseProtocol` does not implement. On the first `drain()` call after writing the `initialize` response, an `AttributeError` is raised, caught silently by `_forward_stream`, and the `sock→stdout` bridge task exits. `asyncio.wait(FIRST_COMPLETED)` then cancels the other direction and the proxy process terminates. MCP clients using `--broker-spawn` or `--broker-connect` (e.g. Zed) receive the `initialize` response but never receive a `tools/list` reply, showing 0 tools. Fixed by replacing `asyncio.BaseProtocol` with `asyncio.StreamReaderProtocol` (which inherits `FlowControlMixin` and implements `_drain_helper`) in `_make_stdout_writer`. Also fixed a pre-existing test isolation issue in `TestBrokerProxyBasic` that caused flaky failures when a live broker was running.
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/proxy.py` — `_make_stdout_writer` fixed
  - `tests/unit/test_broker_stubs.py` — test isolation fixed (temp socket path)
- **Acceptance Criteria:**
  - [x] `_make_stdout_writer` uses `asyncio.StreamReaderProtocol` (not `asyncio.BaseProtocol`)
  - [x] A proxy session forwarding `initialize` → `notifications/initialized` → `tools/list` returns 20 tools without the proxy exiting early
  - [x] All existing broker tests pass (715 passed, 5 skipped)
  - [x] MCP clients in broker mode (e.g. Zed with `--broker-spawn`) show the correct tool count

### Phase 4: Broker Lifecycle Management

#### ✅ P4-T2: Cache tools/list in broker and gate client responses on upstream readiness
- **Status:** ✅ Completed (2026-03-06)
- **Description:** The broker currently forwards `tools/list` to the upstream on every client request with no buffering. This creates a race: when the upstream (xcrun mcpbridge) is still initializing or waiting for Xcode approval, a client's `tools/list` gets no reply or an empty one, which the client caches as "0 tools". The fix has two parts: (1) **Upstream readiness gate** — after spawning the upstream, the broker waits for a successful `initialize` round-trip before accepting or processing further client requests; if the upstream exits immediately (e.g. Xcode dialog not yet approved), the broker retries with backoff instead of forwarding the failure to clients. (2) **tools/list response cache** — after upstream initialization succeeds, the broker immediately fetches and caches the `tools/list` response; subsequent client `tools/list` requests are served from cache; cache is invalidated and refreshed on upstream reconnect. Together these eliminate the Xcode first-approval race: the broker is silent to clients until the upstream is truly ready, and once ready the tools list is served instantly from cache.
- **Priority:** P1
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/daemon.py` — upstream readiness gate (wait for initialize before processing client requests); retry-with-backoff on upstream early exit
  - `src/mcpbridge_wrapper/broker/transport.py` or `daemon.py` — `tools/list` response cache; cache invalidation on upstream reconnect
  - `tests/unit/test_broker_daemon.py` — readiness gate and cache tests
  - `tests/unit/test_broker_transport.py` — cache hit/miss/invalidation tests
- **Acceptance Criteria:**
  - [x] Broker does not forward client requests to upstream until a successful `initialize` round-trip completes
  - [x] If upstream exits before `initialize` completes, broker retries (with backoff) without returning an error to already-connected clients
  - [x] After upstream initializes, broker fetches and stores `tools/list` response in memory cache
  - [x] Client `tools/list` requests are answered from cache (no upstream round-trip needed per client)
  - [x] Cache is cleared and refreshed when upstream reconnects after EOF
  - [x] Zed (or any MCP client) connecting immediately after broker start receives the correct tool count without requiring a manual reload
  - [x] All existing quality gates pass (`pytest`, `ruff`, `mypy`, coverage >= 90%)

#### ✅ P4-T1: Auto-restart stale broker daemon on version mismatch after upgrade
- **Status:** ✅ Completed (2026-03-05)
- **Description:** When users upgrade mcpbridge-wrapper, the old broker daemon keeps running with the old binary. New `--broker` clients silently connect to the stale daemon instead of using updated code. Fix by: (1) fixing version source of truth (`__init__.py` uses `importlib.metadata` from `pyproject.toml`), (2) daemon writes `broker.version` file on startup, (3) proxy checks version before connecting and auto-restarts mismatched daemons, (4) adding `--broker-stop` and `--broker-status` CLI commands, (5) install/uninstall scripts stop running daemons, (6) updating broker-mode docs.
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/__init__.py` — `importlib.metadata`-based `__version__`
  - `src/mcpbridge_wrapper/broker/types.py` — `version_file` property on `BrokerConfig`
  - `src/mcpbridge_wrapper/broker/daemon.py` — version file write/cleanup/status
  - `src/mcpbridge_wrapper/broker/proxy.py` — `_check_version_mismatch()`, `_stop_stale_daemon()`
  - `src/mcpbridge_wrapper/__main__.py` — `--broker-stop`, `--broker-status` CLI commands
  - `scripts/install.sh` — stop running broker on install
  - `scripts/uninstall.sh` — stop running broker on uninstall
  - `docs/broker-mode.md` — CLI commands and version management section
- **Acceptance Criteria:**
  - [x] `__version__` derived from `importlib.metadata` (single source: `pyproject.toml`)
  - [x] Daemon writes `~/.mcpbridge_wrapper/broker.version` on start and cleans on stop
  - [x] Proxy auto-restarts daemon when version file mismatches current `__version__`
  - [x] No version file (old daemon) is treated as compatible (backwards-compatible)
  - [x] `--broker-status` prints daemon PID, version, mismatch warning
  - [x] `--broker-stop` sends SIGTERM, waits, and cleans up state files
  - [x] `scripts/install.sh` stops running broker daemon before writing new wrapper
  - [x] `scripts/uninstall.sh` stops running broker daemon before removing files
  - [x] `docs/broker-mode.md` documents `--broker-stop`, `--broker-status`, and version management
  - [x] All quality gates pass (`pytest`, `ruff`, `mypy`, coverage >= 90%)

### Phase 5: Release

#### ✅ P5-T2: Release 0.4.1 to PyPI and MCP Registry
- **Status:** ✅ Completed (2026-03-06)
- **Description:** Prepare patch release `v0.4.1` by bumping package metadata, documenting the BUG-T9 fix in `CHANGELOG.md`, validating all quality gates, and archiving the release task for merge. The tag push and registry publication remain post-merge human actions.
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `pyproject.toml` — version bumped to `0.4.1`
  - `server.json` — version bumped to `0.4.1`
  - `CHANGELOG.md` — `[0.4.1]` entry added with release date `2026-03-06`
  - `SPECS/ARCHIVE/P5-T2_Release_0.4.1_to_PyPI_and_MCP_Registry/` — archived PRD + validation report
  - (Post-merge, human action) `git tag v0.4.1` push triggers CI/CD PyPI + MCP Registry publish
- **Acceptance Criteria:**
  - [x] `pyproject.toml` and `server.json` version fields are `0.4.1`
  - [x] `CHANGELOG.md` has a `[0.4.1]` entry with the correct release date
  - [ ] `git tag v0.4.1` exists on `main` and is pushed to remote (requires human action post-merge)
  - [ ] `pip install mcpbridge-wrapper==0.4.1` succeeds from PyPI (requires human action post-merge)
  - [ ] `uvx mcpbridge-wrapper --version` reports `0.4.1` (requires human action post-merge)
  - [ ] MCP Registry entry reflects `0.4.1` (auto-triggered by tag push via CI/CD)
  - [ ] README version badge displays `v0.4.1` after PyPI publish propagates (auto after tag push)
  - [x] All quality gates pass (`pytest`, `ruff`, `mypy`, coverage >= 90%`)

#### ✅ P5-T1: Release 0.4.0 to PyPI and MCP Registry
- **Status:** ✅ Completed (2026-03-06)
- **Description:** Tag `v0.4.0` in git, publish the package to PyPI, and update the MCP Registry entry so users can install the latest release via `pip`, `uvx`, and the MCP Registry. Update the CHANGELOG release date to match the actual tag date, trigger or verify CI/CD publish workflows, and confirm the published artifacts are correct.
- **Priority:** P0
- **Dependencies:** P1-T1, P1-T11, P2-T1, P2-T2, P2-T3, P2-T4, P2-T5, P2-T6, P3-T11, P4-T1, P4-T2, BUG-T8
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `CHANGELOG.md` — release date updated to `2026-03-06` (was placeholder `2026-02-20`)
  - `SPECS/INPROGRESS/P5-T1_Validation_Report.md` — all quality gates verified PASS
  - `SPECS/ARCHIVE/P5-T1_release_0.4.0/` — archived PRD + validation report
  - (Post-merge, human action) `git tag v0.4.0` push triggers CI/CD PyPI + MCP Registry publish
- **Acceptance Criteria:**
  - [x] `CHANGELOG.md` `[0.4.0]` entry date matches the actual release date (`2026-03-06`)
  - [ ] `git tag v0.4.0` exists on `main` and is pushed to remote (requires human action post-merge)
  - [ ] `pip install mcpbridge-wrapper==0.4.0` succeeds from PyPI (requires human action post-merge)
  - [ ] `uvx mcpbridge-wrapper[webui] --version` reports `0.4.0` (requires human action post-merge)
  - [ ] MCP Registry entry reflects `0.4.0` (auto-triggered by tag push via CI/CD)
  - [ ] README version badge displays `v0.4.0` after PyPI publish propagates (auto after tag push)
  - [x] All quality gates pass on the tagged commit (`pytest` 785 tests, 90.91% coverage, `ruff`, `mypy`, DocC sync, package assets check)

### Phase 6: Explicit Broker Frontend

#### ✅ P6-T1: Add explicit broker runtime status surface for frontend consumers
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Add a structured runtime status surface for the persistent broker so explicit frontends do not need to infer daemon health from pid files and log parsing alone. The surface should expose broker lifecycle state, upstream pid/availability, client session counts, and other operator-facing details that explain whether the daemon is healthy, reconnecting, or awaiting approval.
- **Priority:** P1
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/daemon.py` runtime status payload extended with readiness, upstream-health, and connected-client details
  - `src/mcpbridge_wrapper/webui/server.py` new `GET /api/broker/status` endpoint for frontend consumers
  - `src/mcpbridge_wrapper/__main__.py` broker-daemon Web UI wiring updated to publish live runtime status
  - `tests/unit/test_broker_daemon.py`, `tests/unit/webui/test_server.py`, and `tests/unit/test_main.py` covering healthy and degraded runtime status flows
- **Acceptance Criteria:**
  - [x] Dedicated broker host exposes structured runtime status including broker state, daemon pid, upstream pid (when present), version, and connected client count
  - [x] Status makes reconnecting/not-ready states explicit so a frontend can distinguish them from a healthy shared daemon
  - [x] Automated tests cover both healthy and degraded broker runtime status responses

#### ✅ P6-T2: Build a terminal frontend for broker daemon monitoring and control
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Implement a terminal-first operator interface for the broker daemon so users can explicitly see whether the daemon is running, whether upstream Xcode connectivity is healthy, which clients are attached, and what recent reconnect/error events occurred. The interface should give a clearer operational model than auto-spawn alone.
- **Priority:** P1
- **Dependencies:** P6-T1
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/tui.py` terminal frontend for broker monitoring and stop control
  - `src/mcpbridge_wrapper/__main__.py` CLI wiring for `--tui`
  - `tests/unit/test_tui.py` and `tests/unit/test_main_tui.py` covering runtime resolution, rendering, control requests, and CLI integration
- **Acceptance Criteria:**
  - [x] Users can launch a terminal UI from the wrapper package to inspect broker runtime state without tailing logs manually
  - [x] The TUI shows at minimum broker state, daemon/upstream PIDs, connected client count, and recent broker events or reconnect indicators
  - [x] The TUI exposes at least one explicit control action for the daemon lifecycle (for example stop or restart)

#### ✅ P6-T3: Document the explicit dedicated-host frontend workflow
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Update the operator docs so the recommended path for multi-editor setups is an explicit dedicated broker host plus a single monitoring frontend. The docs should explain when to prefer a dedicated host over implicit auto-spawn, how to verify that both editors share one daemon, and how the new frontend fits into that workflow.
- **Priority:** P2
- **Dependencies:** P6-T1, P6-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` dedicated-host guidance updated to mention the explicit frontend
  - `docs/broker-mode.md` and related docs updated with the recommended monitoring/control workflow
  - Any new frontend usage documentation added under `docs/`
- **Acceptance Criteria:**
  - [x] README explains the dedicated-host + frontend workflow for users who want explicit visibility into daemon health
  - [x] Broker docs describe how to confirm that multiple editors are attached to one shared daemon
  - [x] Frontend launch and troubleshooting steps are documented in a user-facing guide

### Phase 7: Broker UX and Diagnostics

#### ✅ P7-T1: Add one-command broker host startup with attached frontend
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Add a single operator-facing command that starts the dedicated broker host, ensures the dashboard endpoint is owned by that host, and immediately opens the terminal frontend against the same runtime. The goal is to remove the current multi-step manual sequence of starting the daemon, checking the port, and launching TUI separately.
- **Priority:** P0
- **Dependencies:** P6-T1, P6-T2
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/__main__.py` or new orchestration module with a one-command startup path such as `--broker-console`
  - `src/mcpbridge_wrapper/tui.py` integration adjustments so the frontend can attach to the just-started host without a race
  - `tests/unit/test_main_tui.py` and related tests covering startup orchestration and error messaging
- **Acceptance Criteria:**
  - [x] Users can run one command to start broker mode in the recommended dedicated-host workflow and immediately land in a working frontend
  - [x] The command either starts the broker-hosted dashboard successfully or surfaces a precise actionable error before opening the frontend
  - [x] The implementation avoids requiring users to manually sequence `--broker-daemon`, `--web-ui`, and `--tui`

#### ✅ FU-P7-T1-1: Normalize KeyboardInterrupt handling when broker-console reuses an existing host
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Align `--broker-console` exit behavior when it attaches to an already healthy broker-backed dashboard. Today the spawn path normalizes `KeyboardInterrupt` to exit code `0`, but the reuse-existing-dashboard path returns `run_tui(runtime)` directly and lets `Ctrl-C` bubble out differently from both `--tui` mode and the spawned console path.
- **Priority:** P1
- **Dependencies:** P7-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/__main__.py` reuse path updated to handle `KeyboardInterrupt` consistently
  - regression coverage in `tests/unit/test_main.py` or `tests/unit/test_main_tui.py`
- **Acceptance Criteria:**
  - [x] `--broker-console` returns exit code `0` on `KeyboardInterrupt` whether it spawns a host or reuses an existing broker-backed dashboard
  - [x] Unit tests cover the reuse-existing-dashboard interrupt path

#### ✅ P7-T2: Implement a broker doctor command for cross-black-box diagnostics
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Add a `doctor`-style diagnostic command that inspects the full chain visible to the user: Python package/runtime, local broker files and processes, dashboard endpoint ownership, upstream Xcode bridge state when observable, and common failure modes such as stale ports, missing dashboard, version mismatch, or wrong endpoint. The output should help users debug without needing to understand the internal architecture first.
- **Priority:** P0
- **Dependencies:** P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/__main__.py` CLI wiring for a `doctor` or equivalent diagnostics command
  - new diagnostics module that checks broker PID/socket/version files, HTTP endpoints, occupied ports, and current package/runtime identity
  - unit/integration tests covering healthy, missing-dashboard, wrong-port, and stale-runtime scenarios
- **Acceptance Criteria:**
  - [x] A single command prints a concise diagnosis of broker health and the most likely next action when startup failed
  - [x] The diagnostics distinguish between “broker alive but no dashboard”, “dashboard alive but wrong service”, “port already occupied”, and “broker not running”
  - [x] Output is user-facing and actionable without requiring users to manually run `lsof`, `curl`, or inspect raw log files first

#### ✅ P7-T3: Auto-recover or guide on dashboard port ownership conflicts
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Remove the silent partial state where `--broker-daemon --web-ui` can keep a broker alive without the requested dashboard. Startup now fails fast with one explicit remediation path or points users at the already-healthy broker-backed frontend, while `--broker-console --web-ui-restart` remains the safe recovery path for occupied ports.
- **Priority:** P0
- **Dependencies:** P6-T1, P7-T2
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - broker startup/orchestration flow updated to fail fast on unusable dashboard ports instead of silently degrading
  - improved stderr guidance aligned with the dedicated-host `doctor` / broker-console workflow
  - tests covering foreign listeners, running brokers without dashboards, healthy existing dashboards, and restart-assisted recovery
- **Acceptance Criteria:**
  - [x] Users are not left with a running broker that silently lacks the dashboard/frontend required by the recommended UX path
  - [x] Port conflicts result in either automatic safe recovery or one explicit remediation path with exact commands or next steps
  - [x] TUI and diagnostics clearly explain the conflict source and whether the current runtime is usable

#### ✅ FU-P7-T3-1: Prioritize foreign port-owner guidance in mixed broker/dashboard conflicts
- **Status:** ✅ Completed (2026-03-07)
- **Description:** When startup sees both a live broker PID and a non-broker listener on the requested dashboard port, current remediation prioritizes broker reset guidance and can hide the actual foreign port owner. Update startup and diagnostics conflict ordering so users see the real blocker or one combined recovery path instead of being sent into a reset loop.
- **Priority:** P1
- **Dependencies:** P7-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - mixed-state broker/dashboard conflict classifier or message ordering updates
  - startup and diagnostics tests covering live broker PID plus foreign dashboard-port listener
  - any wording changes needed so recovery stays explicit and single-path
- **Acceptance Criteria:**
  - [x] `--broker-console` and `--broker-daemon --web-ui` surface the foreign dashboard-port owner or both blockers when a live broker PID and foreign listener coexist
  - [x] `--doctor` does not hide the foreign listener behind a generic broker-without-dashboard diagnosis in the same mixed state
  - [x] Regression tests cover the mixed-state conflict and prevent reordering back to broker-only guidance

#### ✅ FU-P7-T3-2: Exclude broker-owned dashboard listeners from foreign port-conflict guidance
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Refine the mixed broker/dashboard conflict classifier so it distinguishes the broker daemon's own dashboard listener from a foreign process on the same port. When degraded probes occur against a broker-owned listener, startup and diagnostics should keep users on broker-health guidance instead of reporting a foreign port owner.
- **Priority:** P1
- **Dependencies:** FU-P7-T3-1
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/__main__.py` mixed-state startup guidance that filters broker-owned listener PIDs out of foreign-conflict messaging
  - `src/mcpbridge_wrapper/doctor.py` mixed-state diagnostic guidance with the same broker-owned listener exclusion
  - `tests/unit/test_main.py` and `tests/unit/test_doctor.py` regression coverage for foreign-listener and broker-owned-listener mixed states
- **Acceptance Criteria:**
  - [x] Mixed-state foreign-port guidance triggers only when the dashboard listener PID differs from the running broker PID
  - [x] Broker-owned listeners with degraded dashboard probes do not tell users to stop an "existing listener" or use restart guidance meant for foreign ownership
  - [x] Regression tests cover both foreign-listener and broker-owned-listener mixed states in startup and doctor paths

#### ✅ P7-T4: Add direct local-status fallback for TUI when dashboard API is unavailable
- **Description:** Reduce TUI dependence on the Web UI API by letting it fall back to local broker state when the dashboard endpoint is unavailable. The TUI should still provide useful diagnostics from PID/socket/version files and any directly accessible broker status sources, while clearly indicating that live dashboard-backed controls are unavailable.
- **Priority:** P1
- **Dependencies:** P6-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/tui.py` local fallback mode for unavailable dashboard API
  - any supporting runtime/status helpers needed to expose broker health without HTTP
  - tests covering unavailable dashboard with live broker, dead broker, and degraded-control states
- **Acceptance Criteria:**
  - [x] TUI remains useful when the dashboard API is down and still shows the best available local broker diagnosis
  - [x] The screen clearly distinguishes live dashboard-backed runtime data from local fallback data
  - [x] Users can tell from TUI alone whether they need to restart the broker, free a port, or just attach a client

#### ✅ P7-T5: Document the simplest supported broker UX and failure recovery flow
- **Status:** ✅ Completed (2026-03-07)
- **Description:** After the orchestration and diagnostics improvements land, rewrite the user-facing docs around the simplest supported broker UX. The docs should present one recommended command path first, then one short failure-recovery path using the new diagnostic surfaces, instead of forcing users to piece together behavior from multiple guides.
- **Priority:** P1
- **Dependencies:** P7-T1, P7-T2, P7-T3, P7-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `docs/quickstart.md` — new minimal end-to-end guide (5 steps)
  - `docs/broker-mode.md` — restructured with quickstart-first and failure recovery sections
  - `docs/troubleshooting.md` — updated to reference quickstart and `--doctor`
- **Acceptance Criteria:**
  - [x] New users can find the recommended broker startup command and the recommended diagnostic command within one short reading path
  - [x] The docs no longer require users to infer the relationship between broker, dashboard, TUI, and Xcode approval prompts from multiple separate pages
  - [x] Failure recovery steps are written around the new UX primitives rather than raw manual shell debugging

### Phase 8: Release

#### ✅ P8-T1: Release version 0.4.2 to PyPI and MCP Registry
- **Status:** ✅ Completed (2026-03-07)
- **Description:** Cut the `0.4.2` release to publish all Phase 5–7 work (broker console, doctor diagnostics, port-conflict recovery, TUI local fallback, broker UX docs). Bumped version in `pyproject.toml` and `server.json` to `0.4.2`, updated the README version badge, committed. Git tag `v0.4.2` to be pushed to `origin` after PR merges to trigger `publish-mcp.yml`.
- **Priority:** P0
- **Dependencies:** P7-T5
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `pyproject.toml` version set to `0.4.2`
  - `server.json` version set to `0.4.2`
  - `README.md` version badge updated to `v0.4.2`
  - Git tag `v0.4.2` pushed to `origin` (post-merge)
  - `publish-mcp.yml` workflow completed successfully (post-merge)
- **Acceptance Criteria:**
  - [x] `pyproject.toml` and `server.json` both contain version `0.4.2`
  - [x] README version badge reflects `v0.4.2`
  - [ ] Git tag `v0.4.2` exists on `origin/main` (post-merge)
  - [ ] `https://pypi.org/project/mcpbridge-wrapper/0.4.2/` is accessible (post-merge)
  - [ ] GitHub Actions `publish-mcp.yml` run for tag `v0.4.2` shows all steps green (post-merge)

#### ✅ P8-T2: Prepare for Release 0.4.3
- **Status:** ✅ Completed (2026-03-10)
- **Description:** Prepared patch release `0.4.3` for the work merged after `v0.4.2`, covering the broker warmed-tool-catalog readiness fix (`P2-T8`) and the editable-install troubleshooting guidance (`P1-T13`). Bumped release metadata to `0.4.3`, synced the README and DocC overview badges, added changelog release notes, and validated the full local pre-release gate suite. Tagging and publication remain post-merge actions on `main`.
- **Priority:** P0
- **Dependencies:** P1-T13, P2-T8
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `pyproject.toml` — version set to `0.4.3`
  - `server.json` — root and package versions set to `0.4.3`
  - `README.md` and `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` — version badges updated to `v0.4.3`
  - `CHANGELOG.md` — `[0.4.3]` entry added for `P2-T8` and `P1-T13`
  - `SPECS/ARCHIVE/P8-T2_Prepare_for_Release_0.4.3/` — archived PRD + validation report
  - (Post-merge, human action) `git tag v0.4.3` push triggers PyPI + MCP Registry publish
- **Acceptance Criteria:**
  - [x] `pyproject.toml` and `server.json` both contain version `0.4.3`
  - [x] `README.md` version badge reflects `v0.4.3`
  - [x] `CHANGELOG.md` contains a `[0.4.3]` entry dated `2026-03-10` covering the release contents
  - [x] `pytest tests/ -v --cov=src --cov-report=term`, `ruff check src/ tests/`, `ruff format --check src/ tests/`, `mypy src/`, `make doccheck-all`, `python -m build`, and `twine check dist/*` all pass
  - [ ] Git tag `v0.4.3` exists on `origin/main` (post-merge)
  - [ ] `https://pypi.org/project/mcpbridge-wrapper/0.4.3/` is accessible (post-merge)
  - [ ] GitHub Actions `publish-mcp.yml` run for tag `v0.4.3` shows all steps green (post-merge)

#### ✅ P8-T3: Prepare for Release 0.4.4
- **Status:** ✅ Completed (2026-03-10)
- **Description:** Prepared patch release `0.4.4` for the work merged after `v0.4.3`, covering the Xcode approval observation harness (`T-010`) and the broker-side synthetic `notifications/tools/list_changed` warm-up notification (`T-011`). Bumped release metadata to `0.4.4`, synced the README and DocC overview badges, added changelog release notes, and validated the full local pre-release gate suite from `PUBLISHING.md`. Tagging and publication remain post-merge actions on `main`.
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `pyproject.toml` — version set to `0.4.4`
  - `server.json` — root and package versions set to `0.4.4`
  - `README.md` and `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` — version badges updated to `v0.4.4`
  - `CHANGELOG.md` — `[0.4.4]` entry added for `T-010` and `T-011`
  - `SPECS/ARCHIVE/P8-T3_Prepare_for_Release_0.4.4/` — archived PRD + validation report
  - (Post-merge, human action) `git tag v0.4.4` push triggers PyPI + MCP Registry publish
- **Acceptance Criteria:**
  - [x] `pyproject.toml` and `server.json` both contain version `0.4.4`
  - [x] `README.md` and `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` both reflect `v0.4.4`
  - [x] `CHANGELOG.md` contains a `[0.4.4]` entry dated `2026-03-10` covering `T-010` and `T-011`
  - [x] `pytest tests/ -v --cov=src --cov-report=term`, `ruff check src/ tests/`, `ruff format --check src/ tests/`, `mypy src/`, `make doccheck-all`, `python -m build`, and `twine check dist/*` all pass
  - [ ] Git tag `v0.4.4` exists on `origin/main` (post-merge)
  - [ ] `https://pypi.org/project/mcpbridge-wrapper/0.4.4/` is accessible (post-merge)
  - [ ] GitHub Actions `publish-mcp.yml` run for tag `v0.4.4` shows all steps green (post-merge)
