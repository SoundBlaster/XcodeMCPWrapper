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

#### ⬜️ P1-T10: Document Xcode first-approval timing race in Troubleshooting & Known Issues
- **Description:** When broker mode is used for the first time, Xcode shows an approval dialog for the new daemon process. If an MCP client (Zed, Cursor) connects and sends `tools/list` before Xcode grants approval, it receives an empty tools list and caches it — showing 0 tools indefinitely until the user manually reloads the MCP connection. This is a real usability trap: the green dot shows "connected" but 0 tools, with no clear error. Document the root cause, the correct first-time setup sequence, and the recovery steps in `docs/troubleshooting.md` and as a Known Issue in `README.md`. Also note that each unique process identity (direct wrapper vs broker daemon) triggers a separate Xcode dialog.
- **Priority:** P1
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `docs/troubleshooting.md` — new section "Broker mode shows 0 tools on first run (Xcode approval timing)"
  - `README.md` — Known Issues entry for first-approval race condition
  - DocC mirror synced (`Sources/XcodeMCPWrapper/Documentation.docc/`)
- **Acceptance Criteria:**
  - [ ] `docs/troubleshooting.md` describes the symptom (green dot, 0 tools), root cause (Xcode dialog timing race), correct setup sequence (start broker first → approve → then connect clients), and recovery steps (reload MCP in client after approval)
  - [ ] `docs/troubleshooting.md` notes that each new process identity (direct vs broker daemon) triggers a separate Xcode dialog
  - [ ] `README.md` Known Issues section includes this scenario
  - [ ] `make doccheck-all` passes

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

#### ⬜️ P4-T2: Cache tools/list in broker and gate client responses on upstream readiness
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
  - [ ] Broker does not forward client requests to upstream until a successful `initialize` round-trip completes
  - [ ] If upstream exits before `initialize` completes, broker retries (with backoff) without returning an error to already-connected clients
  - [ ] After upstream initializes, broker fetches and stores `tools/list` response in memory cache
  - [ ] Client `tools/list` requests are answered from cache (no upstream round-trip needed per client)
  - [ ] Cache is cleared and refreshed when upstream reconnects after EOF
  - [ ] Zed (or any MCP client) connecting immediately after broker start receives the correct tool count without requiring a manual reload
  - [ ] All existing quality gates pass (`pytest`, `ruff`, `mypy`, coverage >= 90%)

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
