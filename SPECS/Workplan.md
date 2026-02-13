# Workplan: mcpbridge-wrapper

## 1. Overview

### 1.1 Goal
Create a Python-based protocol compatibility wrapper that intercepts MCP responses from Xcode 26.3's `xcrun mcpbridge` and transforms non-compliant responses into MCP-spec-compliant format by injecting the required `structuredContent` field.

### 1.2 Key Assumptions (from PRD §1.4)
- Xcode 26.3+ is installed with MCP bridge enabled
- Python 3.7+ is available (standard macOS installation)
- Target users are developers using Cursor or other strict MCP-spec-compliant clients
- Xcode must be running with a project open for tools to function

### 1.3 Constraints (from PRD §1.4)
- Wrapper must be a single executable Python script for easy distribution
- Response latency overhead must be < 5ms per request (NFR1)
- Memory footprint must be < 10MB (NFR2)
- Must handle concurrent bidirectional I/O (FR10)

### 1.4 Non-Goals
- Do NOT modify Xcode's mcpbridge binary or internal behavior
- Do NOT implement caching or response buffering beyond line-level
- Do NOT create a GUI or interactive configuration tool
- Do NOT support Python versions below 3.7
- Do NOT implement the 20 Xcode MCP tools (only wrap the existing bridge)

---

## 2. Phases

### Phase 1: Foundation & Scaffolding
**Intent:** Establish project structure, Python packaging, and development tooling to support implementation and testing.

### Phase 2: Core Bridge Implementation
**Intent:** Implement the subprocess wrapper around `xcrun mcpbridge` with bidirectional stdin/stdout piping and async I/O handling.

### Phase 3: Response Transformation Engine
**Intent:** Implement JSON parsing, MCP compliance detection, and the `structuredContent` injection logic per PRD §3.1 Functional Requirements.

### Phase 4: Edge Case Handling
**Intent:** Ensure robust handling of all failure scenarios and edge cases documented in PRD §5.1-5.2.

### Phase 5: Testing & Verification
**Intent:** Validate all functional requirements, non-functional requirements, and success criteria through comprehensive unit and integration tests.

### Phase 6: Packaging & Distribution
**Intent:** Create installable artifacts and configuration templates for Cursor, Claude Code, and Codex CLI.

### Phase 7: Documentation
**Intent:** Produce user-facing documentation for installation, configuration, and troubleshooting.

### Phase 10: Web UI Control & Audit Dashboard
**Intent:** Create a web-based dashboard for real-time monitoring, control, and audit logging of the XcodeMCPWrapper.

---

## 3. Tasks

### Phase 1: Foundation & Scaffolding

#### ✅ P1-T1: Create Project Directory Structure
- **Description:** Create `src/mcpbridge_wrapper/`, `tests/unit/`, `tests/integration/`, and `scripts/` directories
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Directory tree structure
  - `src/mcpbridge_wrapper/__init__.py` (empty)
- **Acceptance Criteria:** All directories exist and are importable as Python packages

#### ✅ P1-T2: Initialize Python Project with pyproject.toml
- **Description:** Create `pyproject.toml` with project metadata, Python 3.7+ requirement, and build system configuration
- **Priority:** P0
- **Dependencies:** P1-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `pyproject.toml` with [project], [build-system], and [project.scripts] sections
- **Acceptance Criteria:** `pip install -e .` succeeds and installs the package

#### ✅ P1-T3: Configure Linting and Formatting Tools
- **Description:** Add ruff configuration for linting/formatting and mypy for type checking in pyproject.toml
- **Priority:** P1
- **Dependencies:** P1-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Linting rules in `pyproject.toml`
  - `.pre-commit-config.yaml` (optional)
- **Acceptance Criteria:** `ruff check src/` runs without configuration errors

#### ✅ P1-T4: Set up pytest Configuration
- **Description:** Configure pytest with coverage reporting in pyproject.toml
- **Priority:** P0
- **Dependencies:** P1-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `[tool.pytest.ini_options]` and `[tool.coverage.run]` in pyproject.toml
- **Acceptance Criteria:** `pytest --version` reads config without errors; `pytest` runs (even with 0 tests)

#### ✅ P1-T5: Create Makefile with Common Tasks
- **Description:** Add Makefile targets for test, lint, format, typecheck, and install
- **Priority:** P2
- **Dependencies:** P1-T3, P1-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `Makefile` with targets: test, lint, format, typecheck, install, clean
- **Acceptance Criteria:** `make test` runs pytest; `make lint` runs ruff check

#### ✅ P1-T6: Add Python .gitignore
- **Description:** Create .gitignore with standard Python patterns (venv, __pycache__, *.pyc, etc.)
- **Priority:** P1
- **Dependencies:** P1-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `.gitignore` file
- **Acceptance Criteria:** `git status` does not show Python cache files or virtual environment directories

---

### Phase 2: Core Bridge Implementation

#### ✅ P2-T1: Implement Subprocess Bridge to xcrun mcpbridge
- **Description:** Create subprocess.Popen wrapper that launches `xcrun mcpbridge` with stdin/stdout pipes per PRD §3.1 FR1-FR2
- **Priority:** P0
- **Dependencies:** P1-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `src/mcpbridge_wrapper/bridge.py` with `create_bridge()` function
- **Acceptance Criteria:** Function returns a Popen object with readable stdout and writable stdin; process starts without errors when Xcode is running

#### ✅ P2-T2: Implement Stdin Forwarding Loop
- **Description:** Forward all stdin lines from wrapper process to mcpbridge stdin unmodified per PRD §3.1 FR2
- **Priority:** P0
- **Dependencies:** P2-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `forward_stdin()` function in `bridge.py`
- **Acceptance Criteria:** Raw bytes from sys.stdin appear identically on bridge.stdin; manual test with echo confirms passthrough

#### ✅ P2-T3: Implement Stdout Capture with Line Buffering
- **Description:** Read stdout from bridge line-by-line with bufsize=1 (line buffering) per PRD §3.1 FR9
- **Priority:** P0
- **Dependencies:** P2-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `read_stdout()` generator function in `bridge.py`
- **Acceptance Criteria:** Each yielded item is a complete line (ends with newline); no partial line buffering issues

#### ✅ P2-T4: Add Daemon Thread for Async Stdout Reading
- **Description:** Spawn daemon thread that runs stdout reader to prevent blocking main thread per PRD §3.1 FR10
- **Priority:** P0
- **Dependencies:** P2-T3
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Thread spawning logic in `bridge.py`
  - Queue for thread-safe line passing
- **Acceptance Criteria:** Main thread can continue processing while stdout is being read; thread terminates when bridge exits

#### ✅ P2-T5: Implement Stderr Passthrough
- **Description:** Pass stderr from bridge directly to wrapper's stderr without modification
- **Priority:** P1
- **Dependencies:** P2-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - stderr forwarding in subprocess.Popen call
- **Acceptance Criteria:** Error messages from mcpbridge appear on terminal immediately

#### ✅ P2-T6: Handle Bridge Process Lifecycle
- **Description:** Implement startup verification, clean shutdown on exit, and exit code propagation
- **Priority:** P1
- **Dependencies:** P2-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `cleanup()` function; exit code handling in main
- **Acceptance Criteria:** Wrapper exits with same code as mcpbridge; no zombie processes left

#### ✅ P2-T7: Forward Command-Line Arguments
- **Description:** Pass sys.argv[1:] to mcpbridge subprocess to support any bridge arguments
- **Priority:** P1
- **Dependencies:** P2-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Argument forwarding in Popen args list
- **Acceptance Criteria:** Running `wrapper --help` shows mcpbridge help output

---

### Phase 3: Response Transformation Engine

#### ✅ P3-T1: Implement JSON Detection Logic
- **Description:** Detect whether a line is valid JSON or plain text per PRD §3.1 FR3
- **Priority:** P0
- **Dependencies:** P2-T3
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `is_json_line()` function in `src/mcpbridge_wrapper/transform.py`
- **Acceptance Criteria:** Returns True for `{"key": "value"}`; Returns False for `Plain text log`

#### ✅ P3-T2: Implement JSON Parsing with Error Handling
- **Description:** Parse JSON lines with try/except; re-raise or handle decode errors per PRD §3.1 FR3
- **Priority:** P0
- **Dependencies:** P3-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `parse_json_safe()` function returning (success, data) tuple
- **Acceptance Criteria:** Valid JSON returns (True, dict); Invalid JSON returns (False, original_line)

#### ✅ P3-T3: Detect Non-Compliant Responses
- **Description:** Identify responses with `content` field but missing `structuredContent` per PRD §3.1 FR4
- **Priority:** P0
- **Dependencies:** P3-T2
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `needs_transformation()` function checking result object structure
- **Acceptance Criteria:** Returns True for `{"result": {"content": []}}`; Returns False if `structuredContent` exists

#### ✅ P3-T4: Extract Text from Content Array
- **Description:** Find first content item with `type: "text"` and extract its `text` field per PRD §3.1 FR5
- **Priority:** P0
- **Dependencies:** P3-T3
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `extract_text_content()` function
- **Acceptance Criteria:** Given `[{"type": "image"}, {"type": "text", "text": "data"}]`, returns `"data"`; returns None if no text items

#### ✅ P3-T5: Parse Extracted Text as JSON
- **Description:** Attempt to parse extracted text content as JSON object per PRD §3.1 FR6
- **Priority:** P0
- **Dependencies:** P3-T4
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `parse_structured_content()` function
- **Acceptance Criteria:** `{"result": true}` string becomes dict; `"plain string"` becomes string primitive; invalid JSON raises exception

#### ✅ P3-T6: Implement Fallback Wrapper for Invalid JSON
- **Description:** On JSON decode error, wrap text in `{"text": content}` structure per PRD §3.1 FR7
- **Priority:** P1
- **Dependencies:** P3-T5
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Fallback logic in `parse_structured_content()` or caller
- **Acceptance Criteria:** Non-JSON text `"error message"` becomes `{"text": "error message"}`

#### ✅ P3-T7: Inject structuredContent into Result
- **Description:** Add `structuredContent` field to result object with parsed JSON value per PRD §3.1 FR6-FR7
- **Priority:** P0
- **Dependencies:** P3-T5, P3-T6
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `inject_structured_content()` function
- **Acceptance Criteria:** Input `{"result": {"content": [{"text": "{}"}]}}` becomes `{"result": {"content": [...], "structuredContent": {}}}`

#### ✅ P3-T8: Implement Non-JSON Output Passthrough
- **Description:** Pass through non-JSON lines (logs, errors) unmodified per PRD §3.1 FR8
- **Priority:** P1
- **Dependencies:** P3-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Branch in main processing loop for passthrough
- **Acceptance Criteria:** Plain text lines appear on stdout unchanged and unwrapped

#### ✅ P3-T9: Implement Unbuffered Output
- **Description:** Use `flush=True` on all stdout write operations per PRD §3.1 FR9
- **Priority:** P0
- **Dependencies:** P3-T7, P3-T8
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `print(..., flush=True)` or `sys.stdout.write()` with explicit flush
- **Acceptance Criteria:** Responses appear immediately (no buffering delay visible)

#### ✅ P3-T10: Implement Main Response Processing Loop
- **Description:** Combine all transformation components into line_processor function per PRD §4.2
- **Priority:** P0
- **Dependencies:** P2-T4, P3-T7, P3-T8, P3-T9
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `process_response_line()` function
  - `main()` entry point in `src/mcpbridge_wrapper/__main__.py`
- **Acceptance Criteria:** End-to-end: stdin → bridge → transform → stdout; all PRD test cases pass

---

### Phase 4: Edge Case Handling

#### ✅ P4-T1: Handle Empty Content Array
- **Description:** Pass through responses with `"content": []` without modification per PRD §5.1
- **Priority:** P1
- **Dependencies:** P3-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Empty list check in `needs_transformation()`
- **Acceptance Criteria:** `{"result": {"content": []}}` is passed through unchanged

#### ✅ P4-T2: Handle Content with No Text Items
- **Description:** Pass through responses with only image or non-text content types per PRD §5.2 EC3
- **Priority:** P1
- **Dependencies:** P3-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - None-found handling in `extract_text_content()`
- **Acceptance Criteria:** `[{"type": "image", "url": "..."}]` results in no transformation

#### ✅ P4-T3: Handle Already Compliant Responses
- **Description:** Pass through responses that already have `structuredContent` field per PRD §5.2 EC2
- **Priority:** P1
- **Dependencies:** P3-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Presence check in `needs_transformation()`
- **Acceptance Criteria:** `{"structuredContent": {...}}` responses are not modified

#### ✅ P4-T4: Handle Responses Without Result Field
- **Description:** Pass through JSON objects that don't have a `result` key (notifications, errors)
- **Priority:** P1
- **Dependencies:** P3-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Field existence check in `needs_transformation()`
- **Acceptance Criteria:** `{"id": 1, "error": null}` is passed through unchanged

#### ✅ P4-T5: Handle Bridge Process Crash
- **Description:** Detect bridge process termination and exit with same exit code per PRD §5.1
- **Priority:** P1
- **Dependencies:** P2-T6
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Exit code propagation in main loop
- **Acceptance Criteria:** When mcpbridge exits with code 1, wrapper also exits with code 1

#### ✅ P4-T6: Handle Client Disconnect
- **Description:** Cleanly shutdown when stdin closes (client disconnects) per PRD §5.1
- **Priority:** P1
- **Dependencies:** P2-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - EOF detection in stdin forwarding loop (already implemented)
  - Validation report confirming graceful shutdown
- **Acceptance Criteria:** Wrapper terminates gracefully when stdin pipe is closed

#### ✅ P4-T7: Handle Malformed JSON from Bridge
- **Description:** Pass through unparseable JSON lines unchanged per PRD §5.1
- **Priority:** P1
- **Dependencies:** P3-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Exception handling returning original line
- **Acceptance Criteria:** Partial JSON `{"broken` is output exactly as received

#### ✅ P4-T8: Handle Nested JSON String Content
- **Description:** Correctly handle text content that is a valid JSON string primitive per PRD §5.2 EC4
- **Priority:** P2
- **Dependencies:** P3-T5
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Test case in test suite
- **Acceptance Criteria:** Text `"plain string"` becomes `structuredContent: "plain string"` (not error)

#### ✅ P4-T9: Handle Very Large JSON Responses
- **Description:** Ensure memory-efficient processing for large JSON payloads (>1MB)
- **Priority:** P2
- **Dependencies:** P2-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Line-based processing (no buffering entire response)
- **Acceptance Criteria:** Can process 10MB JSON line without MemoryError; memory stays <10MB

---

### Phase 5: Testing & Verification

#### ✅ P5-T1: Create Unit Test Framework
- **Description:** Set up pytest structure with fixtures for common test data
- **Priority:** P0
- **Dependencies:** P1-T4
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `tests/unit/__init__.py`, `conftest.py` with fixtures
- **Acceptance Criteria:** `pytest tests/unit` runs without import errors
- **Status:** COMPLETED (2026-02-08)

#### ✅ P5-T2: Write Test for Valid Transformation (TC1)
- **Description:** Test response with content, no structuredContent gets injected per PRD §7.1 TC1
- **Priority:** P0
- **Dependencies:** P3-T7, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_valid_transformation`
- **Acceptance Criteria:** Test passes; coverage includes `process_response_line`

#### ✅ P5-T3: Write Test for Already Compliant Response (TC2)
- **Description:** Test response with both fields remains unmodified per PRD §7.1 TC2
- **Priority:** P0
- **Dependencies:** P4-T3, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_already_compliant`
- **Acceptance Criteria:** Output JSON equals input JSON exactly

#### ✅ P5-T4: Write Test for Non-JSON Text Content (TC3)
- **Description:** Test fallback to `{"text": content}` wrapper per PRD §7.1 TC3
- **Priority:** P0
- **Dependencies:** P3-T6, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_non_json_text_fallback`
- **Acceptance Criteria:** `structuredContent` equals `{"text": "plain text"}`

#### ✅ P5-T5: Write Test for Non-JSON Line Passthrough (TC4)
- **Description:** Test plain text stdout lines pass through unmodified per PRD §7.1 TC4
- **Priority:** P0
- **Dependencies:** P3-T8, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_non_json_passthrough`
- **Acceptance Criteria:** Plain text input equals output exactly

#### ✅ P5-T6: Write Test for Empty Content Array (TC5)
- **Description:** Test `{"content": []}` passes through unmodified per PRD §7.1 TC5
- **Priority:** P1
- **Dependencies:** P4-T1, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_empty_content`
- **Acceptance Criteria:** No transformation applied to empty content

#### ✅ P5-T7: Write Test for No Result Field (TC6)
- **Description:** Test non-result JSON passes through per PRD §7.1 TC6
- **Priority:** P1
- **Dependencies:** P4-T4, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_no_result_field`
- **Acceptance Criteria:** Notifications/error objects unchanged

#### ✅ P5-T8: Write Test for Mixed Content Types (EC1)
- **Description:** Test image + text content array extracts first text per PRD §5.2 EC1
- **Priority:** P1
- **Dependencies:** P3-T4, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_mixed_content`
- **Acceptance Criteria:** First text item extracted despite preceding image

#### ✅ P5-T9: Write Test for Nested JSON String (EC4)
- **Description:** Test `"plain string"` becomes valid structuredContent per PRD §5.2 EC4
- **Priority:** P2
- **Dependencies:** P4-T8, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_json_string_primitive`
- **Acceptance Criteria:** String primitive preserved in structuredContent

#### ✅ P5-T10: Create Integration Test with Mock Bridge
- **Description:** Create mock mcpbridge process for end-to-end testing
- **Priority:** P0
- **Dependencies:** P2-T1, P3-T10, P5-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `tests/integration/test_e2e.py`
  - Mock bridge fixture that outputs canned responses
- **Acceptance Criteria:** Full stdin→transform→stdout cycle verified

#### ✅ P5-T11: Implement Performance Benchmark
- **Description:** Time 1000 transformations to verify <5ms overhead per PRD §3.1 NFR1
- **Priority:** P1
- **Dependencies:** P3-T10, P5-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/integration/test_performance.py`
  - Benchmark report with average latency
- **Acceptance Criteria:** Average overhead <5ms; documented in test output

#### ✅ P5-T12: Test with Real Xcode mcpbridge (Manual)
- **Description:** Manual integration test with actual Xcode 26.3+ running
- **Priority:** P0
- **Dependencies:** P3-T10
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Test results document
- **Acceptance Criteria:** No errors during 5-minute continuous operation

#### ✅ P5-T13: Verify All 20 Xcode MCP Tools (IT1-IT4)
- **Description:** Test each of the 20 tools listed in PRD §3.1 tool list
- **Priority:** P0
- **Dependencies:** P5-T12
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Integration test suite covering all tools
- **Acceptance Criteria:** Each tool returns valid structuredContent without -32600 errors

#### ✅ P5-T14: Achieve 90%+ Code Coverage
- **Description:** Run coverage report and fill gaps to reach 90% line coverage
- **Priority:** P1
- **Dependencies:** P5-T2 through P5-T11
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Coverage report HTML
  - Missing coverage addressed
- **Acceptance Criteria:** `pytest --cov` shows ≥90% coverage

---

### Phase 6: Packaging & Distribution

#### ✅ P6-T1: Create Standalone Executable Script
- **Description:** Create single-file `mcpbridge-wrapper` script suitable for `~/bin` installation
- **Priority:** P0
- **Dependencies:** P3-T10
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `src/mcpbridge_wrapper/cli.py` or standalone `mcpbridge-wrapper`
- **Acceptance Criteria:** File runs directly: `./mcpbridge-wrapper`; all imports self-contained

#### ✅ P6-T2: Add Executable Shebang and Permissions
- **Description:** Add `#!/usr/bin/env python3` and ensure file is executable per PRD §3.4
- **Priority:** P0
- **Dependencies:** P6-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Executable bit set on script file
- **Acceptance Criteria:** `ls -l` shows `x` permission; runs without `python` prefix

#### ✅ P6-T3: Create Installation Script
- **Description:** Create shell script that installs to `~/bin/mcpbridge-wrapper`
- **Priority:** P1
- **Dependencies:** P6-T2
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `scripts/install.sh`
- **Acceptance Criteria:** Running `scripts/install.sh` creates `~/bin/mcpbridge-wrapper`; script is executable

#### ✅ P6-T4: Create Cursor MCP Configuration Template
- **Description:** Create `~/.cursor/mcp.json` configuration example per PRD §6.1
- **Priority:** P0
- **Dependencies:** P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `config/cursor-mcp.json` example file
  - Documentation snippet
- **Acceptance Criteria:** JSON is valid; path uses `$HOME` or documents username replacement

#### ✅ P6-T5: Create Claude Code Configuration Template
- **Description:** Document `claude mcp add` command for Claude Code per PRD §3.4
- **Priority:** P2
- **Dependencies:** P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Configuration snippet in docs
- **Acceptance Criteria:** Command `claude mcp add --transport stdio xcode -- /Users/$USER/bin/mcpbridge-wrapper` is documented

#### ✅ P6-T6: Create Codex CLI Configuration Template
- **Description:** Document `codex mcp add` command for Codex CLI per PRD §3.4
- **Priority:** P2
- **Dependencies:** P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Configuration snippet in docs
- **Acceptance Criteria:** Command `codex mcp add xcode -- /Users/$USER/bin/mcpbridge-wrapper` is documented

#### ✅ P6-T7: Configure pip Installable Package
- **Description:** Ensure `pip install` creates executable entry point
- **Priority:** P2
- **Dependencies:** P1-T2, P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `[project.scripts]` entry in pyproject.toml
- **Acceptance Criteria:** After `pip install`, `mcpbridge-wrapper` command is available in PATH

#### ✅ P6-T8: Create GitHub Release Workflow
- **Description:** GitHub Actions workflow to create releases with attached artifacts
- **Priority:** P3
- **Dependencies:** P1-T8, P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `.github/workflows/release.yml`
- **Acceptance Criteria:** Pushing tag creates release with downloadable script

#### ✅ P6-T9: Create Uninstall Script
- **Description:** Create uninstall script to remove mcpbridge-wrapper from ~/bin and pip
- **Priority:** P2
- **Dependencies:** P6-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `scripts/uninstall.sh` - Removes wrapper script from ~/bin, uninstalls pip package, optionally cleans config
- **Acceptance Criteria:** 
  - Running `scripts/uninstall.sh` removes `~/bin/mcpbridge-wrapper`
  - pip uninstalls the mcpbridge-wrapper package
  - Script has dry-run mode and confirmation prompts

#### ✅ P6-T10: Create GitHub CI Workflow
- **Description:** Create GitHub Actions workflow for continuous integration that checks project state: build, tests, lint, typecheck
- **Priority:** P1
- **Dependencies:** P1-T2, P1-T3, P1-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `.github/workflows/ci.yml`
- **Acceptance Criteria:** 
  - Workflow triggers on push/PR to main
  - Runs lint (ruff check)
  - Runs format check (ruff format --check)
  - Runs type check (mypy)
  - Runs tests with pytest across Python 3.9-3.12
  - Builds package and validates with twine
  - All checks must pass

---

### Phase 7: Documentation

#### ✅ P7-T1: Write Installation Guide Section
- **Description:** Document step-by-step installation for end users per PRD §4.1
- **Priority:** P0
- **Dependencies:** P6-T3
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `docs/installation.md` or README section
- **Acceptance Criteria:** New user can follow instructions without external help

#### ✅ P7-T2: Write Cursor Configuration Guide
- **Description:** Document GUI and JSON configuration for Cursor per PRD §4.1
- **Priority:** P0
- **Dependencies:** P6-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/cursor-setup.md`
- **Acceptance Criteria:** Cursor successfully loads xcode-tools after following guide

#### ✅ P7-T3: Write Claude Code Configuration Guide
- **Description:** Document one-liner setup for Claude Code
- **Priority:** P1
- **Dependencies:** P6-T5
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/claude-setup.md` or combined doc
- **Acceptance Criteria:** `claude mcp list` shows xcode-tools after setup

#### ✅ P7-T4: Write Codex CLI Configuration Guide
- **Description:** Document one-liner setup for Codex CLI
- **Priority:** P1
- **Dependencies:** P6-T6
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/codex-setup.md` or combined doc
- **Acceptance Criteria:** `codex mcp list` shows xcode-tools after setup

#### ✅ P7-T5: Document Environment Variables
- **Description:** Document `MCP_XCODE_PID` and `MCP_XCODE_SESSION_ID` per PRD §6.2
- **Priority:** P1
- **Dependencies:** P2-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Environment variables table in documentation
- **Acceptance Criteria:** User understands when and how to use optional environment variables

#### ✅ P7-T6: Write Troubleshooting Guide
- **Description:** Document common errors and solutions per PRD §4.3
- **Priority:** P1
- **Dependencies:** P4-T1 through P4-T9
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/troubleshooting.md` covering -32600 error and others
- **Acceptance Criteria:** Each error has symptom, cause, and solution clearly documented

#### ✅ P7-T7: Document the 20 Xcode MCP Tools
- **Description:** List and briefly describe all available tools per PRD tool list
- **Priority:** P2
- **Dependencies:** P5-T13
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Tool reference table in documentation
- **Acceptance Criteria:** All 20 tools documented with name and description

#### ✅ P7-T8: Write Architecture Overview
- **Description:** Document how the wrapper works internally for contributors
- **Priority:** P2
- **Dependencies:** P3-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/architecture.md` with diagrams
- **Acceptance Criteria:** Reader understands data flow from stdin to stdout

#### ✅ P7-T9: Create Usage Examples
- **Description:** Document sample workflows (build, test, read file)
- **Priority:** P2
- **Dependencies:** P5-T13
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Example commands in documentation
- **Acceptance Criteria:** 3+ practical examples with expected output

#### ✅ P7-T10: Write Final README
- **Description:** Complete README with all essential information
- **Priority:** P0
- **Dependencies:** P7-T1, P7-T2, P7-T6
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `README.md` at project root
- **Acceptance Criteria:** README includes: what, why, install, configure, usage, troubleshoot

#### ✅ P7-T11: Create CHANGELOG
- **Description:** Document version history and changes
- **Priority:** P2
- **Dependencies:** P7-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `CHANGELOG.md` with initial 1.0.0 entry
- **Acceptance Criteria:** Follows Keep a Changelog format; all phases summarized

#### ✅ P7-T12: Move Cursor IDE uvx settings before installation instructions in README
- **Description:** Reorder the README.md so that the Cursor IDE uvx configuration snippet (currently under Configuration > Cursor > "Using uvx (Recommended)") appears before the Installation section. This gives Cursor users the fastest path to getting started — they only need to paste the JSON block into `~/.cursor/mcp.json` and they're done, without scrolling through five installation options first. Include both the basic uvx snippet and the uvx-with-Web-UI variant (`--web-ui`, `--web-ui-port 8080`) so users can choose either option up front.
- **Priority:** P1
- **Dependencies:** P7-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - Updated `README.md` with reordered sections
- **Acceptance Criteria:**
  - The Cursor uvx `mcp.json` snippet (basic) is visible in the README before the "Installation" heading
  - The Cursor uvx-with-Web-UI `mcp.json` snippet (`--web-ui`, `--web-ui-port 8080`) is also shown alongside the basic snippet
  - All other README content (installation options, other client configs, usage, etc.) remains intact and in a logical order
  - No broken markdown links or formatting issues

---

### Phase 8: Documentation Publishing

**Intent:** Set up automated documentation generation and publishing using Apple DocC for hosting on GitHub Pages.

#### ✅ P8-T1: Support Apple DocC for documentation and publishing on soundblaster.github.io Pages
- **Description:** Configure Apple DocC to generate documentation and publish to GitHub Pages at soundblaster.github.io/XcodeMCPWrapper (superseding the original `/mcpbridge-wrapper` path target).
- **Priority:** P2
- **Dependencies:** P7-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - DocC documentation catalog (`.docc`)
  - GitHub Actions workflow for automated publishing (`.github/workflows/docs.yml`)
  - Published docs at `soundblaster.github.io/XcodeMCPWrapper`
- **Acceptance Criteria:** 
  - DocC builds documentation without errors
  - GitHub Pages site is live at `soundblaster.github.io/XcodeMCPWrapper/`
  - Documentation updates automatically on pushes to main

#### ✅ P8-T2: Restructure DocC to Canonical Swift Package Format
- **Description:** Move DocC catalog from root-level `mcpbridge-wrapper.docc/` to canonical Swift Package Manager structure under `Sources/XcodeMCPWrapper/Documentation.docc/`
- **Priority:** P2
- **Dependencies:** P8-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - New directory: `Sources/XcodeMCPWrapper/Documentation.docc/`
  - Main DocC file: `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`
  - All existing DocC articles moved to new location
  - Updated GitHub Actions workflow with correct paths
- **Acceptance Criteria:** 
  - DocC catalog follows Apple's canonical SPM structure
  - GitHub Actions workflow builds from new location
  - All existing documentation content preserved
  - GitHub Pages deployment still works correctly
  - Old `mcpbridge-wrapper.docc/` directory removed
- **Canonical Structure:**
  ```
  Sources/
    XcodeMCPWrapper/
      Documentation.docc/
        XcodeMCPWrapper.md          # Main landing page
        GettingStarted.md
        Installation.md
        Configuration.md
        CursorSetup.md
        ClaudeCodeSetup.md
        CodexCLISetup.md
        Troubleshooting.md
        Architecture.md
        EnvironmentVariables.md
  ```
- **Reference Implementation:**
  ```yaml
  name: Deploy DocC Documentation
  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]
    workflow_dispatch:
  permissions:
    contents: read
    pages: write
    id-token: write
  concurrency:
    group: "pages"
    cancel-in-progress: false
  jobs:
    build:
      runs-on: macos-14
      steps:
        - uses: actions/checkout@v4
        - uses: maxim-lobanov/setup-xcode@v1
          with:
            xcode-version: latest-stable
        - name: Build Documentation
          run: |
            swift package --allow-writing-to-directory ./docs \
              generate-documentation \
              --target mcpbridge-wrapper \
              --output-path ./docs \
              --transform-for-static-hosting \
              --hosting-base-path mcpbridge-wrapper
        - name: Add .nojekyll and index.html redirect
          run: |
            touch docs/.nojekyll
            cat > docs/index.html << 'EOF'
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <title>Redirecting to mcpbridge-wrapper Documentation</title>
              <meta http-equiv="refresh" content="0; url=./documentation/mcpbridgewrapper/">
              <link rel="canonical" href="./documentation/mcpbridgewrapper/">
            </head>
            <body>
              <p>Redirecting to <a href="./documentation/mcpbridgewrapper/">mcpbridge-wrapper Documentation</a>...</p>
              <script>
                window.location.href = "./documentation/mcpbridgewrapper/";
              </script>
            </body>
            </html>
            EOF
        - uses: actions/upload-pages-artifact@v3
          if: github.event_name == 'push'
          with:
            path: "./docs"
    deploy:
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      needs: build
      runs-on: ubuntu-latest
      environment:
        name: github-pages
        url: ${{ steps.deployment.outputs.page_url }}
      steps:
        - id: deployment
          uses: actions/deploy-pages@v4
  ```

#### ✅ P8-T3: Change Deployment Path to xcodemcpwrapper
- **Description:** Update all public-facing documentation, scripts, and configuration templates to use the new deployment path `/Users/YOUR_USERNAME/bin/xcodemcpwrapper` instead of `/Users/YOUR_USERNAME/bin/mcpbridge-wrapper`. The Python package name (`mcpbridge_wrapper`) remains unchanged - only the deployed executable name changes.
- **Priority:** P1
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Updated `scripts/install.sh` - Creates `~/bin/xcodemcpwrapper` instead of `~/bin/mcpbridge-wrapper`
  - Updated `scripts/uninstall.sh` - Removes `~/bin/xcodemcpwrapper`
  - Updated `config/cursor-mcp.json` - New path in JSON template
  - Updated `config/claude-code.txt` - New path in command examples
  - Updated `config/codex-cli.txt` - New path in command examples
  - Updated `config/zed-agent.json` - New path in JSON template
  - Updated `README.md` - All path references
  - Updated `AGENTS.md` - Configuration examples
  - Updated `CONTRIBUTING.md` - Development references
  - Updated `docs/*.md` - All documentation files
  - Updated `Sources/XcodeMCPWrapper/Documentation.docc/*.md` - DocC documentation
- **Acceptance Criteria:** 
  - All public docs show `xcodemcpwrapper` as the executable name
  - Installation script creates `~/bin/xcodemcpwrapper`
  - Configuration templates use new path
  - No references to `~/bin/mcpbridge-wrapper` remain in active documentation
  - Historical archives (SPECS/ARCHIVE/) are NOT modified
  - Python source code and package names remain unchanged
  - All tests pass after changes

Phase 8 Follow-up Backlog
- [x] FU-P8-T1-1: Reconcile P8-T1 URL criteria with current GitHub Pages path and resolve DocC reference warnings (P2)
- [x] FU-P6-T10-1: Align manual install script with Web UI configuration expectations (P1)

#### ✅ FU-P8-T1-1: Reconcile P8-T1 URL criteria with current GitHub Pages path and resolve DocC reference warnings
- **Description:** Review follow-up to align Phase 8 tracking artifacts with the live documentation URL `soundblaster.github.io/XcodeMCPWrapper/` and remove remaining DocC ambiguity warnings in the Phase 8 documentation index.
- **Priority:** P2
- **Dependencies:** P8-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - Updated `SPECS/Workplan.md` P8-T1 references to match current GitHub Pages URL
  - Updated Phase 8 validation/review artifacts with an explicit supersession note where applicable
  - Updated `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` DocC links to avoid ambiguous references
- **Acceptance Criteria:**
  - Workplan Phase 8 no longer references the legacy `/mcpbridge-wrapper` GitHub Pages URL as the active deployment URL
  - Phase 8 review/validation artifacts clearly document that the active URL is `soundblaster.github.io/XcodeMCPWrapper/`
  - `swift package generate-documentation --target XcodeMCPWrapper` completes without `Architecture` ambiguity warnings

#### ✅ FU-P6-T10-1: Align manual install script with Web UI configuration expectations
- **Description:** Fix the mismatch where `scripts/install.sh` installs only the base package (`pip install -e .`) while docs/config examples allow `--web-ui` usage from `~/bin/xcodemcpwrapper`. This causes runtime failure when users enable Web UI without optional dependencies. Add an explicit installer mode for Web UI extras and update documentation to make the dependency requirement unambiguous.
- **Priority:** P1
- **Dependencies:** P6-T3, P10-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - Updated `scripts/install.sh` with Web UI-aware install option (e.g., `--webui`) that installs `-e ".[webui]"`
  - Updated `README.md` and `docs/installation.md` with clear mapping:
    - base install => no `--web-ui` args
    - webui install => `--web-ui` args supported
  - Updated `docs/troubleshooting.md` to include this specific symptom/cause/fix path
- **Acceptance Criteria:**
  - Running `./scripts/install.sh` (default) keeps current base behavior and works with no Web UI args
  - Running `./scripts/install.sh --webui` installs required Web UI dependencies (`fastapi`, `uvicorn`, etc.)
  - `~/bin/xcodemcpwrapper --web-ui --web-ui-port 8080 --help` no longer fails after Web UI install mode
  - Zed/Cursor configs that include `--web-ui` work when installer is run with Web UI mode
  - Documentation examples do not imply Web UI works on base-only install

---

## Known Issues / Bug Tracker

### BUG-T0: Uptime widget on Web UI always shows 1h 0m 0s ✅
- **Type:** Bug / Feature Issue
- **Status:** ✅ Complete
- **Priority:** P2
- **Discovered:** 2026-02-13
- **Component:** Web UI Dashboard
- **Affected:** Web UI uptime widget display

#### Description
The uptime widget on the Web UI dashboard always displays a fixed value of "1h 0m 0s" instead of showing the actual runtime uptime of the XcodeMCPWrapper process.

#### Symptoms
```
Uptime widget shows: 1h 0m 0s
Expected: Dynamic uptime that increases over time (e.g., 1h 5m 23s after 5 minutes 23 seconds)
```

#### Root Cause Analysis
[To be diagnosed during implementation]

#### Workaround
The uptime counter in the metrics sidebar may show accurate counts for requests/errors as an alternative indicator of runtime.

#### Resolution Path
- [ ] Investigate Web UI metrics collection and uptime calculation
- [ ] Check if uptime is being calculated as fixed value instead of elapsed time
- [ ] Implement dynamic uptime display
- [ ] Add tests for uptime widget accuracy over time
- [ ] Verify dashboard updates correctly

---

### BUG-T1: Kimi CLI MCP Connection Failure
- **Type:** Bug / Compatibility Issue
- **Status:** 🔴 Open - Client-Side Issue
- **Priority:** P2
- **Discovered:** 2026-02-08
- **Component:** Client Compatibility
- **Affected Client:** Kimi CLI v1.9.0
- **Working Clients:** Cursor, Zed Agent, Claude Code, Codex CLI

#### Description
Kimi CLI (v1.9.0) fails to maintain a stable stdio MCP connection with `xcodemcpwrapper`. The connection initializes successfully but is immediately closed with error: `Server session was closed unexpectedly`.

#### Symptoms
```
Error running tool: Client failed to connect: Server session was closed unexpectedly
```

#### Verification Results
| Test | Method | Result |
|------|--------|--------|
| Direct wrapper test | `echo '{"jsonrpc":"2.0",...}' \| xcodemcpwrapper` | ✅ Pass |
| Zed Agent integration | `XcodeListWindows` | ✅ Pass |
| Kimi CLI integration | `XcodeListWindows` | ❌ Fail |

#### Root Cause Analysis
The wrapper correctly implements MCP protocol spec and responds properly:
```json
{"id":1,"jsonrpc":"2.0","result":{"capabilities":{"tools":{"listChanged":true}},"protocolVersion":"2024-11-05","serverInfo":{"name":"xcode-tools","version":"24571"}}}
```

The issue appears to be in Kimi CLI's stdio MCP transport/session management, not the wrapper itself.

#### Workaround
Use alternative MCP clients that work correctly:
- ✅ **Zed Agent** - Tested and verified working
- ✅ **Cursor** - Primary target client, fully supported
- ✅ **Claude Code** - Documented and tested
- ✅ **Codex CLI** - Documented and tested

#### Resolution Path
- [ ] Report issue to Kimi CLI development team
- [ ] Monitor Kimi CLI updates for MCP transport fixes
- [ ] Document limitation in troubleshooting guide
- [ ] Re-test when Kimi CLI v1.10.0+ is released

#### References
- Kimi CLI version tested: 1.9.0
- Wrapper version tested: 0.1.7
- Related: P5-T13 (Tool verification across clients)

---

### Phase 10: Web UI Control & Audit Dashboard

**Intent:** Create a web-based dashboard for real-time monitoring, control, and audit logging of the XcodeMCPWrapper. Provides visibility into MCP tool usage, performance metrics, and operational control.

#### ✅ P10-T1: Implement Web UI Control & Audit Dashboard

**Description:**
Create a comprehensive web dashboard for monitoring and controlling the XcodeMCPWrapper. The dashboard will provide real-time metrics (RPS, latency, error rates), tool usage analytics with visualizations, request/response inspector for debugging, persistent audit logging, and service control interface. Implement using FastAPI for the backend with WebSocket support for live updates, and a modern HTML/CSS/JS frontend with Chart.js visualizations. Include configurable authentication, log rotation, and export capabilities.

**Priority:** P1

**Dependencies:** P9-T1

**Parallelizable:** no

**Outputs/Artifacts:**
- `src/mcpbridge_wrapper/webui/` package with:
  - `server.py` - FastAPI web server with REST API and WebSocket
  - `metrics.py` - Thread-safe metrics collection system
  - `audit.py` - Structured audit logging with rotation
  - `config.py` - Web UI configuration management
  - `static/` - Frontend dashboard assets (HTML, CSS, JS)
- `config/webui.json` - Configuration template
- Updated `src/mcpbridge_wrapper/cli.py` - Add `--web-ui` flag
- Updated `pyproject.toml` - Optional webui dependencies
- Tests in `tests/unit/webui/` and `tests/integration/webui/`
- Documentation in `docs/webui-setup.md`

**Acceptance Criteria:**
- [ ] Dashboard accessible at `http://localhost:8080` when `--web-ui` flag is used
- [ ] Real-time metrics update via WebSocket every second
- [ ] Tool usage charts (bar, pie, timeline) display accurate data
- [ ] Audit logs capture all MCP tool calls with timestamps
- [ ] Log export produces valid JSON/CSV files
- [ ] Web UI has < 1% performance impact on wrapper core
- [ ] All existing tests pass with Web UI enabled
- [ ] New unit tests achieve > 90% coverage for webui module
- [ ] Documentation includes setup and troubleshooting guide
- [ ] Optional authentication works correctly
- [ ] Log rotation prevents unbounded disk usage

**Sub-tasks:**
1. P10-T1.1: Create webui package structure and metrics collection hooks
2. P10-T1.2: Implement FastAPI server with REST endpoints and WebSocket
3. P10-T1.3: Build frontend dashboard with Chart.js visualizations
4. P10-T1.4: Implement audit logging with rotation
5. P10-T1.5: Add CLI integration and configuration
6. P10-T1.6: Write tests and documentation

---

#### ✅ P10-T2: Fix Web UI timeseries charts showing no data

**Description:**
The Web UI dashboard shows "Connected" and counters work correctly, but the timeseries charts ("Request timeline" and "Latency") show no data. The issue is that `SharedMetricsStore.get_timeseries()` returns data in a different format than the frontend expects:

- **Current (wrong):** `{"data": [{"timestamp": "...", "requests": N, "errors": N, "latency_ms": N}]}`
- **Expected by frontend:** `{"requests": [{"t": seconds_ago, "v": count}], "errors": [...], "latencies": [{"t": seconds_ago, "v": latency}]}`

The frontend JavaScript expects arrays of `{t, v}` objects for each metric type, with time as "seconds ago" relative to now. The SharedMetricsStore currently returns minute-bucketed data with string timestamps.

**Root Cause:**
When migrating from in-memory `MetricsCollector` (which had the correct format) to `SharedMetricsStore` (SQLite-based for multi-process support), the `get_timeseries()` method was implemented with a different return format that doesn't match the frontend expectations.

**Priority:** P1

**Dependencies:** P10-T1

**Parallelizable:** no

**Outputs/Artifacts:**
- Fixed `src/mcpbridge_wrapper/webui/shared_metrics.py` - Update `get_timeseries()` to return format matching frontend expectations
- Updated tests in `tests/unit/webui/test_shared_metrics.py` - Verify timeseries format
- Validation report confirming charts display data correctly

**Acceptance Criteria:**
- [ ] `/api/metrics/timeseries` returns data in format `{"requests": [...], "errors": [...], "latencies": [...]}`
- [ ] Each array contains objects with `t` (seconds ago) and `v` (value) properties
- [ ] Request timeline chart displays data points
- [ ] Latency chart displays data points
- [ ] Charts update in real-time via WebSocket
- [ ] All existing tests pass
- [ ] New tests verify timeseries format matches frontend expectations

---

#### ✅ P10-T3: Recover main branch after accidental Web UI merge

**Description:**
Main branch is currently unstable after an accidental merge of the Phase 10 Web UI branch. Diagnose regressions introduced by that merge and restore main to a releasable state without discarding intended Web UI functionality.

**Priority:** P0

**Dependencies:** P10-T2

**Parallelizable:** no

**Outputs/Artifacts:**
- Regression report listing failures introduced by the accidental merge
- Corrective patch set (revert and/or forward-fix) to restore stability
- Updated tests/docs where behavior changed during stabilization

**Acceptance Criteria:**
- [ ] `pytest` passes on the recovery branch
- [ ] `ruff check src/` and `mypy src/` pass
- [ ] Web UI functionality from P10 remains operational after stabilization
- [ ] No known merge-regression failures remain on the branch proposed for `main`

---

### Phase 9: Release Management

**Intent:** Manage version releases, including version bumps, changelog updates, and automated publishing.

#### ✅ P9-T2: Update Documentation with uvx Installation Method
- **Description:** Update all documentation to include uvx as the recommended installation method. The package is now published to PyPI and MCP Registry, and uvx provides the easiest way to install without cloning the repository or manually setting up paths. Update README.md, all docs/*.md files, AGENTS.md, and config templates with uvx instructions.
- **Priority:** P1
- **Dependencies:** P9-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Updated `README.md` - Primary uvx method documented, manual install as alternative
  - Updated `docs/installation.md` - uvx installation section
  - Updated `docs/cursor-setup.md` - uvx configuration examples
  - Updated `docs/claude-setup.md` - uvx configuration examples
  - Updated `docs/codex-setup.md` - uvx configuration examples
  - Updated `AGENTS.md` - uvx method in Quick Start
  - Updated `config/cursor-mcp.json` - uvx template option
  - Updated `config/claude-code.txt` - uvx command option
  - Updated `config/codex-cli.txt` - uvx command option
- **Acceptance Criteria:** 
  - All documentation shows uvx as the primary/recommended installation method
  - Manual installation is documented as an alternative for development
  - All config templates include uvx options
  - uvx installation verified working (already tested by user)
  - No breaking changes to existing manual installation paths

---

#### ✅ P9-T1: Release version 0.2.0
- **Description:** Bump version to 0.2.0, update CHANGELOG, create git tag, and trigger automated publishing to PyPI and MCP Registry
- **Priority:** P1
- **Dependencies:** P8-T2
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Version updated in `pyproject.toml` (0.1.7 → 0.2.0)
  - Version updated in `server.json` (0.1.7 → 0.2.0)
  - CHANGELOG.md entry for v0.2.0
  - Git tag `v0.2.0` pushed to origin
  - GitHub Release created automatically
- **Acceptance Criteria:** 
  - `pyproject.toml` shows version 0.2.0
  - `server.json` shows version 0.2.0
  - CHANGELOG has entry for [0.2.0] with release date
  - Git tag `v0.2.0` exists on GitHub
  - GitHub Actions workflow publishes to PyPI successfully
  - MCP Registry receives the new version
- **Release Checklist:**
  - [ ] Update version in `pyproject.toml`
  - [ ] Update version in `server.json`
  - [ ] Add CHANGELOG entry for 0.2.0
  - [ ] Commit changes: "Bump version to 0.2.0"
  - [ ] Create git tag: `git tag v0.2.0`
  - [ ] Push tag: `git push origin v0.2.0`
  - [ ] Verify GitHub Actions workflow completes
  - [ ] Verify PyPI package updated
  - [ ] Verify MCP Registry updated

---

#### ✅ P9-T3: Release version 0.3.0 (Web UI Feature Release)
- **Description:** Prepare and publish version 0.3.0 as the Web UI release. Include final version bumps, release notes for the new dashboard feature set, and tagged publication to PyPI and MCP Registry.
- **Priority:** P1
- **Dependencies:** P10-T3, FU-REBUILD-P10-T1-6
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Version updated in `pyproject.toml` (0.2.0 -> 0.3.0)
  - Version updated in `server.json` (0.2.0 -> 0.3.0)
  - CHANGELOG.md entry for v0.3.0 with Web UI highlights
  - Git tag `v0.3.0` pushed to origin
  - GitHub Release created automatically
- **Acceptance Criteria:** 
  - `pyproject.toml` shows version 0.3.0
  - `server.json` shows version 0.3.0
  - CHANGELOG has entry for [0.3.0] with release date and Web UI feature summary
  - Git tag `v0.3.0` exists on GitHub
  - GitHub Actions workflow publishes to PyPI successfully
  - MCP Registry receives version 0.3.0
- **Release Checklist:**
  - [x] Update version in `pyproject.toml`
  - [x] Update version in `server.json`
  - [x] Add CHANGELOG entry for 0.3.0 (Web UI release)
  - [x] Commit changes: "Bump version to 0.3.0"
  - [x] Create git tag: `git tag v0.3.0`
  - [x] Push tag: `git push origin v0.3.0`
  - [x] Verify GitHub Actions workflow completes
  - [x] Verify PyPI package updated
  - [x] Verify MCP Registry updated

---

Phase 9 Follow-up Backlog
- [x] FU-P9-T2-1: Fix uvx Web UI examples to include `webui` extras (P1)

#### ✅ FU-P9-T2-1: Fix uvx Web UI examples to include `webui` extras
- **Description:** Resolve documentation/config mismatch where examples use `uvx --from mcpbridge-wrapper ... --web-ui` without optional dependencies. Update all uvx Web UI examples to install extras via `--from mcpbridge-wrapper[webui]`, and align troubleshooting/runtime guidance with the correct uvx command.
- **Priority:** P1
- **Dependencies:** P9-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - Updated `README.md` uvx + Web UI snippets use `mcpbridge-wrapper[webui]`
  - Updated `docs/cursor-setup.md`, `docs/claude-setup.md`, `docs/codex-setup.md` uvx + Web UI commands
  - Updated config templates: `config/cursor-mcp.json`, `config/zed-agent.json`, `config/claude-code.txt`, `config/codex-cli.txt`
  - Updated troubleshooting guidance to include uvx extras fix path
  - Optional: improved runtime error message when `--web-ui` is used without extras
- **Acceptance Criteria:**
  - No remaining documented command/config combines `--web-ui` with `uvx --from mcpbridge-wrapper` (base-only)
  - All uvx Web UI examples consistently use `uvx --from mcpbridge-wrapper[webui] mcpbridge-wrapper`
  - A user can copy/paste the documented Cursor JSON Web UI config and connect without `ModuleNotFoundError: uvicorn`
  - Troubleshooting docs include both solutions:
    - use `mcpbridge-wrapper[webui]` for uvx
    - remove `--web-ui` args when dashboard is not needed

---

## 4. Dependency Graph

```
P1-T1 → P1-T2 → P1-T3
  │       │       │
  │       │       └────→ P1-T5
  │       │
  │       └────────────→ P1-T4
  │               │
  │               └────→ P5-T1
  │
  └────────────────────→ P1-T6

P2-T1 → P2-T2 → P2-T4 → P3-T10
  │       │       ▲       │
  │       │       │       ▼
  │       │   P2-T3 → P3-T1 → P3-T2 → P3-T3 → P3-T4 → P3-T5 → P3-T6 → P3-T7
  │       │                       │       │       │       │       │       │
  │       │                       │       │       │       │       │       │
  │       │                       ▼       ▼       ▼       ▼       ▼       ▼
  │       └─────────────────────────────────────────────────────────────────→ P4-T1
  │               │       │       │       │       │       │       │       │
  │               ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼
  │               P4-T4   P4-T2   P4-T3   P4-T4   P4-T8   P4-T9   (done)  (done)
  │
  ├──────────────────────────────────────────────────────────────────────────→ P2-T5
  ├──────────────────────────────────────────────────────────────────────────→ P2-T6
  ├──────────────────────────────────────────────────────────────────────────→ P2-T7
  │
  └──────────────────────────────────────────────────────────────────────────→ P5-T10

P3-T8 ─────────────────────────────────────────────────────────────────────→ P3-T10
P3-T9 ─────────────────────────────────────────────────────────────────────→ P3-T10

P5-T1 → P5-T2, P5-T3, P5-T4, P5-T5, P5-T6, P5-T7, P5-T8, P5-T9 (parallel)

P5-T10 → P5-T11
  │
  └────→ P5-T12 → P5-T13

P3-T10, P4-T1-P4-T9 → P6-T1 → P6-T2 → P6-T3
  │                    │       │
  │                    │       └────────────────────────────────────────────→ P7-T1
  │                    │
  │                    ├────────────────────────────────────────────────────→ P6-T4 → P7-T2
  │                    ├────────────────────────────────────────────────────→ P6-T5 → P7-T3
  │                    ├────────────────────────────────────────────────────→ P6-T6 → P7-T4
  │                    └────────────────────────────────────────────────────→ P6-T7

P2-T1 → P7-T5
P3-T10 → P7-T8
P5-T13 → P7-T7, P7-T9
P7-T1, P7-T2, P7-T6 → P7-T10 → P7-T11
```

---

## 5. Traceability Matrix

| PRD Section | Requirement | Task IDs |
|-------------|-------------|----------|
| §1.2 D1 | mcpbridge-wrapper script | P6-T1, P6-T2 |
| §1.2 D2 | Installation documentation | P7-T1 |
| §1.2 D3 | Configuration examples | P6-T4, P6-T5, P6-T6, P7-T2, P7-T3, P7-T4 |
| §1.3 S1 | Cursor compatibility | P5-T13 |
| §1.3 S2 | Transparency | P5-T10, P5-T12 |
| §1.3 S3 | Performance <5ms | P3-T10, P5-T11 |
| §1.3 S4 | 100% valid JSON success | P3-T2, P4-T7, P5-T2-P5-T7 |
| §3.1 FR1 | Intercept all stdout | P2-T3, P2-T4 |
| §3.1 FR2 | Forward stdin unmodified | P2-T2 |
| §3.1 FR3 | Parse JSON responses | P3-T1, P3-T2 |
| §3.1 FR4 | Detect missing structuredContent | P3-T3, P4-T3 |
| §3.1 FR5 | Extract text from content | P3-T4, P4-T2 |
| §3.1 FR6 | Parse text as JSON | P3-T5 |
| §3.1 FR7 | Fallback wrapper | P3-T6, P5-T4 |
| §3.1 FR8 | Passthrough non-JSON | P3-T8, P5-T5 |
| §3.1 FR9 | Unbuffered output | P3-T9 |
| §3.1 FR10 | Concurrent bidirectional I/O | P2-T4 |
| §3.1 NFR1 | Latency <5ms | P3-T10, P5-T11 |
| §3.1 NFR2 | Memory <10MB | P4-T9 |
| §5.1 | Error handling scenarios | P4-T1, P4-T5, P4-T6, P4-T7 |
| §5.2 | Edge cases EC1-EC4 | P5-T8, P5-T9 |
| §7.1 | Unit test cases TC1-TC6 | P5-T2-P5-T7 |
| §7.2 | Integration test IT1-IT4 | P5-T10, P5-T12, P5-T13 |

---

## 6. Execution Checklist

**Status: ✅ COMPLETE - 2026-02-08**

Before starting implementation, verify:
- [x] Xcode 26.3+ is available for testing (P5-T12) - documented as manual test
- [x] Python 3.7+ is installed - verified 3.10.19
- [x] Target `~/bin` directory is writable - install script handles this

During execution:
- [x] P5-T12 (real Xcode test) documented as manual test procedure
- [x] P5-T11 (performance) passed - 0.0023ms avg (well under 5ms)
- [x] All P0 tasks complete - 100% (25/25 tasks)

Completion criteria:
- [x] All P0 tasks: 100% complete (25/25)
- [x] All P1 tasks: 100% complete (29/29)
- [x] P5-T14 coverage: 98.2% (exceeds 90% requirement)
- [x] P5-T13: All 20 tools documented for manual verification
- [x] P5-T11: <5ms overhead verified (0.0023ms avg)

Post-Completion Validation:
- [x] P8-T3 validated: Installation with new path `xcodemcpwrapper` tested successfully
- [x] Client compatibility verified: Zed Agent ✅, Cursor ✅, Claude Code ✅, Codex CLI ✅
- [x] FU-REBUILD-P10-T1-4 completed: Web UI argument examples documented for Zed, Cursor, Claude Code, and Codex CLI (2026-02-11)
- [ ] Known issue documented: Kimi CLI v1.9.0 has MCP connection issues (BUG-T1)

Phase 10: Web UI Dashboard
- [x] P10-T1: Web UI Control & Audit Dashboard (P1)
- [x] P10-T2: Fix Web UI timeseries charts showing no data
- [x] P10-T3: Recover main branch after accidental Web UI merge (P0)
- [x] REBUILD-P10-T1: Spec-driven rebuild package for Web UI feature

Rebuild Follow-up Backlog
- [x] FU-REBUILD-P10-T1-1: Align websocket auth flow between backend and dashboard client (P2)
- [x] FU-REBUILD-P10-T1-2: Add explicit CLI validation/error messaging for invalid --web-ui-port values (P2)
- [x] FU-REBUILD-P10-T1-3: Reconcile docs/webui-setup.md env variable guidance with runtime behavior (P2)
- [x] FU-REBUILD-P10-T1-4: Add Web UI argument examples for client configs (Zed, Cursor, Claude Code, Codex CLI), including `--web-ui` and `--web-ui-port` usage (P2)
- [x] FU-REBUILD-P10-T1-5: Validate and fix documentation paths for local-running MCP server with Web UI (P1)
- [x] FU-REBUILD-P10-T1-6: Fix uninstall.sh package detection/removal asymmetry and venv cleanup (P2)
- [x] FU-REBUILD-P10-T1-7: Include Web UI static assets in published package artifacts (P1)

---

#### ✅ FU-REBUILD-P10-T1-6: Fix uninstall.sh package detection/removal asymmetry and venv cleanup

**Description:**
`scripts/uninstall.sh` has a logic mismatch between detection and removal. Detection checks for both `mcpbridge-wrapper` and `xcodemcpwrapper` pip packages (line 78: `pip3 show mcpbridge-wrapper || pip3 show xcodemcpwrapper`), but the actual uninstall step (line 133) only runs `pip3 uninstall mcpbridge-wrapper -y`. If only `xcodemcpwrapper` were installed as a pip package, the script reports it exists but then tries to uninstall the wrong name. The dry-run output (line 98) also only shows `mcpbridge-wrapper` info.

Additionally, now that `install.sh` creates a `.venv` and embeds the venv Python path in `~/bin/xcodemcpwrapper`, the uninstall script should be updated to handle venv cleanup symmetrically.

**Priority:** P2

**Dependencies:** FU-REBUILD-P10-T1-5

**Parallelizable:** yes

**Problem Analysis:**

1. **Detection/removal asymmetry:** Detection checks two package names but removal only targets one. If `xcodemcpwrapper` is the installed pip name, `pip3 uninstall mcpbridge-wrapper` silently fails or errors.

2. **Dry-run output incomplete:** `pip3 show mcpbridge-wrapper` in dry-run may show nothing even though `xcodemcpwrapper` package is installed — misleading output.

3. **No venv awareness:** After FU-REBUILD-P10-T1-5, `install.sh` now creates a `.venv`. The uninstall script should offer to clean up the venv or at minimum inform the user about it.

**Affected Files:**
- `scripts/uninstall.sh`

**Acceptance Criteria:**
- [ ] Detection and removal are symmetric: uninstall whichever package name is actually installed (or both)
- [ ] Dry-run output accurately reflects which package(s) would be removed
- [ ] Script handles the case where package is installed inside a project `.venv`
- [ ] Existing UX preserved: dry-run, --yes, confirmation flow, clean output

---

#### ✅ FU-REBUILD-P10-T1-5: Validate and fix documentation paths for local-running MCP server with Web UI

**Description:**
Documentation for the "manual installation" / "local running" scenario contains incorrect or misleading paths to the `mcpbridge-wrapper` executable. When a user follows the recommended development setup (creating a `.venv` virtual environment), the package entry point is installed at `.venv/bin/mcpbridge-wrapper`, but the documentation and configuration examples reference `~/bin/xcodemcpwrapper` (a shell wrapper that calls `python3 -m mcpbridge_wrapper` using the system Python, which may not have the package installed).

**Priority:** P1

**Dependencies:** FU-REBUILD-P10-T1-4

**Parallelizable:** yes

**Problem Analysis:**

1. **`install.sh` runs `pip3 install -e .` without activating a venv:** On modern macOS with Homebrew Python, this fails due to PEP 668 (`externally-managed-environment`). The README correctly tells users to create a venv first, but the install script does not use one.

2. **`~/bin/xcodemcpwrapper` wrapper uses system `python3`:** The generated shell script at `~/bin/xcodemcpwrapper` calls `exec python3 -m mcpbridge_wrapper "$@"`. If the package was installed inside `.venv/`, the system `python3` cannot find the `mcpbridge_wrapper` module.

3. **DocC Installation Method 4 is broken:** `Sources/XcodeMCPWrapper/Documentation.docc/Installation.md` suggests `cp src/mcpbridge_wrapper/cli.py ~/bin/xcodemcpwrapper`. This single-file copy cannot work because `cli.py` imports from other modules in the `mcpbridge_wrapper` package.

4. **Configuration examples for manual + Web UI use wrong path:** All config templates (cursor-mcp.json, zed-agent.json, claude-code.txt, codex-cli.txt) and all documentation files show `/Users/YOUR_USERNAME/bin/xcodemcpwrapper` for manual installation. For users who set up via venv (as recommended), the correct path should reference the venv entry point, e.g. `/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper`.

**Affected Files:**
- `scripts/install.sh` - Needs venv-aware installation or correct system-level install
- `config/cursor-mcp.json` - Manual path options
- `config/zed-agent.json` - Manual path options
- `config/claude-code.txt` - Manual path examples
- `config/codex-cli.txt` - Manual path examples
- `README.md` - Manual installation configuration sections
- `docs/installation.md` - Installation methods and paths
- `docs/cursor-setup.md` - Manual installation option
- `docs/claude-setup.md` - Manual installation option
- `docs/codex-setup.md` - Manual installation option
- `docs/webui-setup.md` - Web UI usage examples with manual paths
- `Sources/XcodeMCPWrapper/Documentation.docc/Installation.md` - Method 4 broken copy command
- `Sources/XcodeMCPWrapper/Documentation.docc/CursorSetup.md` - Manual path
- `Sources/XcodeMCPWrapper/Documentation.docc/ClaudeCodeSetup.md` - Manual path
- `Sources/XcodeMCPWrapper/Documentation.docc/CodexCLISetup.md` - Manual path

**Outputs/Artifacts:**
- Fixed `scripts/install.sh` - Either activate venv before pip install, or use the venv Python in the wrapper script
- Updated configuration templates with correct venv-based path option for local development
- Updated all documentation with a clear "Option: Local Development" section showing `.venv/bin/mcpbridge-wrapper` path
- Fixed DocC Installation Method 4 (remove broken single-file copy or replace with correct instructions)
- Validation report confirming all documented paths work end-to-end

**Acceptance Criteria:**
- [ ] `scripts/install.sh` produces a working `xcodemcpwrapper` that can find the `mcpbridge_wrapper` module (either via venv-aware wrapper or correct system install)
- [ ] Configuration examples include a "local development" option with venv path: `<project_path>/.venv/bin/mcpbridge-wrapper`
- [ ] Web UI examples for local development use the correct venv path: `<project_path>/.venv/bin/mcpbridge-wrapper --web-ui --web-ui-port 8080`
- [ ] DocC Installation Method 4 either works correctly or is removed/replaced
- [ ] All existing uvx and pip installation paths remain unchanged and correct
- [ ] All documentation is consistent between README, docs/, config/, and DocC sources
- [ ] A new user following the development setup instructions can successfully run the MCP server locally with Web UI

---

#### ✅ FU-REBUILD-P10-T1-7: Include Web UI static assets in published package artifacts

**Description:**
Users running the published package via `uvx --from mcpbridge-wrapper[webui] mcpbridge-wrapper --web-ui` can start the dashboard server, but `http://localhost:8080` renders:

`XcodeMCPWrapper Dashboard` / `Static files not found.`

Root cause is packaging: the released wheel includes Python modules under `mcpbridge_wrapper/webui/` but omits frontend assets under `mcpbridge_wrapper/webui/static/` (`index.html`, `dashboard.css`, `dashboard.js`). The server falls back to the placeholder HTML when `index.html` is missing.

**Priority:** P1

**Dependencies:** P10-T1, P9-T3

**Parallelizable:** yes

**Outputs/Artifacts:**
- Updated packaging config to include `src/mcpbridge_wrapper/webui/static/*` in wheel/sdist artifacts
- Regression test(s) that fail if dashboard static assets are missing at runtime
- Updated troubleshooting docs with explicit symptom/cause for missing static assets (until patched release is published)
- Patch release plan entry (next version after `0.3.0`) noting Web UI packaging fix

**Acceptance Criteria:**
- [ ] Built wheel contains:
  - `mcpbridge_wrapper/webui/static/index.html`
  - `mcpbridge_wrapper/webui/static/dashboard.css`
  - `mcpbridge_wrapper/webui/static/dashboard.js`
- [ ] `uvx --from mcpbridge-wrapper[webui] mcpbridge-wrapper --web-ui --web-ui-port 8080` serves full dashboard UI (not fallback "Static files not found.")
- [ ] Automated tests cover dashboard HTML serving path and fail on missing static assets
- [ ] Release notes/changelog clearly call out this fix for Web UI users
