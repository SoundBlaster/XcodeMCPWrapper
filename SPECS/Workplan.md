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

### Bug Fixes

#### ⬜️ BUG-T8: Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper
- **Description:** `BrokerProxy._make_stdout_writer` wraps `sys.stdout.buffer` using `asyncio.BaseProtocol` as the protocol, but `asyncio.StreamWriter.drain()` calls `protocol._drain_helper()` which `BaseProtocol` does not implement. On the first `drain()` call after writing the `initialize` response, an `AttributeError` is raised, caught silently by `_forward_stream`, and the `sock→stdout` bridge task exits. `asyncio.wait(FIRST_COMPLETED)` then cancels the other direction and the proxy process terminates. MCP clients using `--broker-spawn` or `--broker-connect` (e.g. Zed) receive the `initialize` response but never receive a `tools/list` reply, showing 0 tools. Fix by replacing `asyncio.BaseProtocol` with `asyncio.StreamReaderProtocol` (which inherits `FlowControlMixin` and implements `_drain_helper`) in `_make_stdout_writer`.
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/proxy.py` — `_make_stdout_writer` fixed
  - Tests updated/added to cover multi-message proxy sessions
- **Acceptance Criteria:**
  - [ ] `_make_stdout_writer` uses `asyncio.StreamReaderProtocol` (not `asyncio.BaseProtocol`)
  - [ ] A proxy session forwarding `initialize` → `notifications/initialized` → `tools/list` returns 20 tools without the proxy exiting early
  - [ ] All existing broker tests pass
  - [ ] MCP clients in broker mode (e.g. Zed with `--broker-spawn`) show the correct tool count
