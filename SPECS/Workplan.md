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

#### P3-T5: Parse Extracted Text as JSON
- **Description:** Attempt to parse extracted text content as JSON object per PRD §3.1 FR6
- **Priority:** P0
- **Dependencies:** P3-T4
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `parse_structured_content()` function
- **Acceptance Criteria:** `{"result": true}` string becomes dict; `"plain string"` becomes string primitive; invalid JSON raises exception

#### P3-T6: Implement Fallback Wrapper for Invalid JSON
- **Description:** On JSON decode error, wrap text in `{"text": content}` structure per PRD §3.1 FR7
- **Priority:** P1
- **Dependencies:** P3-T5
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Fallback logic in `parse_structured_content()` or caller
- **Acceptance Criteria:** Non-JSON text `"error message"` becomes `{"text": "error message"}`

#### P3-T7: Inject structuredContent into Result
- **Description:** Add `structuredContent` field to result object with parsed JSON value per PRD §3.1 FR6-FR7
- **Priority:** P0
- **Dependencies:** P3-T5, P3-T6
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `inject_structured_content()` function
- **Acceptance Criteria:** Input `{"result": {"content": [{"text": "{}"}]}}` becomes `{"result": {"content": [...], "structuredContent": {}}}`

#### P3-T8: Implement Non-JSON Output Passthrough
- **Description:** Pass through non-JSON lines (logs, errors) unmodified per PRD §3.1 FR8
- **Priority:** P1
- **Dependencies:** P3-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Branch in main processing loop for passthrough
- **Acceptance Criteria:** Plain text lines appear on stdout unchanged and unwrapped

#### P3-T9: Implement Unbuffered Output
- **Description:** Use `flush=True` on all stdout write operations per PRD §3.1 FR9
- **Priority:** P0
- **Dependencies:** P3-T7, P3-T8
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `print(..., flush=True)` or `sys.stdout.write()` with explicit flush
- **Acceptance Criteria:** Responses appear immediately (no buffering delay visible)

#### P3-T10: Implement Main Response Processing Loop
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

#### P4-T1: Handle Empty Content Array
- **Description:** Pass through responses with `"content": []` without modification per PRD §5.1
- **Priority:** P1
- **Dependencies:** P3-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Empty list check in `needs_transformation()`
- **Acceptance Criteria:** `{"result": {"content": []}}` is passed through unchanged

#### P4-T2: Handle Content with No Text Items
- **Description:** Pass through responses with only image or non-text content types per PRD §5.2 EC3
- **Priority:** P1
- **Dependencies:** P3-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - None-found handling in `extract_text_content()`
- **Acceptance Criteria:** `[{"type": "image", "url": "..."}]` results in no transformation

#### P4-T3: Handle Already Compliant Responses
- **Description:** Pass through responses that already have `structuredContent` field per PRD §5.2 EC2
- **Priority:** P1
- **Dependencies:** P3-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Presence check in `needs_transformation()`
- **Acceptance Criteria:** `{"structuredContent": {...}}` responses are not modified

#### P4-T4: Handle Responses Without Result Field
- **Description:** Pass through JSON objects that don't have a `result` key (notifications, errors)
- **Priority:** P1
- **Dependencies:** P3-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Field existence check in `needs_transformation()`
- **Acceptance Criteria:** `{"id": 1, "error": null}` is passed through unchanged

#### P4-T5: Handle Bridge Process Crash
- **Description:** Detect bridge process termination and exit with same exit code per PRD §5.1
- **Priority:** P1
- **Dependencies:** P2-T6
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Exit code propagation in main loop
- **Acceptance Criteria:** When mcpbridge exits with code 1, wrapper also exits with code 1

#### P4-T6: Handle Client Disconnect
- **Description:** Cleanly shutdown when stdin closes (client disconnects) per PRD §5.1
- **Priority:** P1
- **Dependencies:** P2-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - EOF detection in stdin forwarding loop
- **Acceptance Criteria:** Wrapper terminates gracefully when stdin pipe is closed

#### P4-T7: Handle Malformed JSON from Bridge
- **Description:** Pass through unparseable JSON lines unchanged per PRD §5.1
- **Priority:** P1
- **Dependencies:** P3-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Exception handling returning original line
- **Acceptance Criteria:** Partial JSON `{"broken` is output exactly as received

#### P4-T8: Handle Nested JSON String Content
- **Description:** Correctly handle text content that is a valid JSON string primitive per PRD §5.2 EC4
- **Priority:** P2
- **Dependencies:** P3-T5
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Test case in test suite
- **Acceptance Criteria:** Text `"plain string"` becomes `structuredContent: "plain string"` (not error)

#### P4-T9: Handle Very Large JSON Responses
- **Description:** Ensure memory-efficient processing for large JSON payloads (>1MB)
- **Priority:** P2
- **Dependencies:** P2-T3
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Line-based processing (no buffering entire response)
- **Acceptance Criteria:** Can process 10MB JSON line without MemoryError; memory stays <10MB

---

### Phase 5: Testing & Verification

#### P5-T1: Create Unit Test Framework
- **Description:** Set up pytest structure with fixtures for common test data
- **Priority:** P0
- **Dependencies:** P1-T4
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `tests/unit/__init__.py`, `conftest.py` with fixtures
- **Acceptance Criteria:** `pytest tests/unit` runs without import errors

#### P5-T2: Write Test for Valid Transformation (TC1)
- **Description:** Test response with content, no structuredContent gets injected per PRD §7.1 TC1
- **Priority:** P0
- **Dependencies:** P3-T7, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_valid_transformation`
- **Acceptance Criteria:** Test passes; coverage includes `process_response_line`

#### P5-T3: Write Test for Already Compliant Response (TC2)
- **Description:** Test response with both fields remains unmodified per PRD §7.1 TC2
- **Priority:** P0
- **Dependencies:** P4-T3, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_already_compliant`
- **Acceptance Criteria:** Output JSON equals input JSON exactly

#### P5-T4: Write Test for Non-JSON Text Content (TC3)
- **Description:** Test fallback to `{"text": content}` wrapper per PRD §7.1 TC3
- **Priority:** P0
- **Dependencies:** P3-T6, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_non_json_text_fallback`
- **Acceptance Criteria:** `structuredContent` equals `{"text": "plain text"}`

#### P5-T5: Write Test for Non-JSON Line Passthrough (TC4)
- **Description:** Test plain text stdout lines pass through unmodified per PRD §7.1 TC4
- **Priority:** P0
- **Dependencies:** P3-T8, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_non_json_passthrough`
- **Acceptance Criteria:** Plain text input equals output exactly

#### P5-T6: Write Test for Empty Content Array (TC5)
- **Description:** Test `{"content": []}` passes through unmodified per PRD §7.1 TC5
- **Priority:** P1
- **Dependencies:** P4-T1, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_empty_content`
- **Acceptance Criteria:** No transformation applied to empty content

#### P5-T7: Write Test for No Result Field (TC6)
- **Description:** Test non-result JSON passes through per PRD §7.1 TC6
- **Priority:** P1
- **Dependencies:** P4-T4, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_no_result_field`
- **Acceptance Criteria:** Notifications/error objects unchanged

#### P5-T8: Write Test for Mixed Content Types (EC1)
- **Description:** Test image + text content array extracts first text per PRD §5.2 EC1
- **Priority:** P1
- **Dependencies:** P3-T4, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_mixed_content`
- **Acceptance Criteria:** First text item extracted despite preceding image

#### P5-T9: Write Test for Nested JSON String (EC4)
- **Description:** Test `"plain string"` becomes valid structuredContent per PRD §5.2 EC4
- **Priority:** P2
- **Dependencies:** P4-T8, P5-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/unit/test_transform.py::test_json_string_primitive`
- **Acceptance Criteria:** String primitive preserved in structuredContent

#### P5-T10: Create Integration Test with Mock Bridge
- **Description:** Create mock mcpbridge process for end-to-end testing
- **Priority:** P0
- **Dependencies:** P2-T1, P3-T10, P5-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `tests/integration/test_e2e.py`
  - Mock bridge fixture that outputs canned responses
- **Acceptance Criteria:** Full stdin→transform→stdout cycle verified

#### P5-T11: Implement Performance Benchmark
- **Description:** Time 1000 transformations to verify <5ms overhead per PRD §3.1 NFR1
- **Priority:** P1
- **Dependencies:** P3-T10, P5-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `tests/integration/test_performance.py`
  - Benchmark report with average latency
- **Acceptance Criteria:** Average overhead <5ms; documented in test output

#### P5-T12: Test with Real Xcode mcpbridge (Manual)
- **Description:** Manual integration test with actual Xcode 26.3+ running
- **Priority:** P0
- **Dependencies:** P3-T10
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Test results document
- **Acceptance Criteria:** No errors during 5-minute continuous operation

#### P5-T13: Verify All 20 Xcode MCP Tools (IT1-IT4)
- **Description:** Test each of the 20 tools listed in PRD §3.1 tool list
- **Priority:** P0
- **Dependencies:** P5-T12
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Integration test suite covering all tools
- **Acceptance Criteria:** Each tool returns valid structuredContent without -32600 errors

#### P5-T14: Achieve 90%+ Code Coverage
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

#### P6-T1: Create Standalone Executable Script
- **Description:** Create single-file `mcpbridge-wrapper` script suitable for `~/bin` installation
- **Priority:** P0
- **Dependencies:** P3-T10
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `src/mcpbridge_wrapper/cli.py` or standalone `mcpbridge-wrapper`
- **Acceptance Criteria:** File runs directly: `./mcpbridge-wrapper`; all imports self-contained

#### P6-T2: Add Executable Shebang and Permissions
- **Description:** Add `#!/usr/bin/env python3` and ensure file is executable per PRD §3.4
- **Priority:** P0
- **Dependencies:** P6-T1
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - Executable bit set on script file
- **Acceptance Criteria:** `ls -l` shows `x` permission; runs without `python` prefix

#### P6-T3: Create Installation Script
- **Description:** Create shell script that installs to `~/bin/mcpbridge-wrapper`
- **Priority:** P1
- **Dependencies:** P6-T2
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `scripts/install.sh`
- **Acceptance Criteria:** Running `scripts/install.sh` creates `~/bin/mcpbridge-wrapper`; script is executable

#### P6-T4: Create Cursor MCP Configuration Template
- **Description:** Create `~/.cursor/mcp.json` configuration example per PRD §6.1
- **Priority:** P0
- **Dependencies:** P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `config/cursor-mcp.json` example file
  - Documentation snippet
- **Acceptance Criteria:** JSON is valid; path uses `$HOME` or documents username replacement

#### P6-T5: Create Claude Code Configuration Template
- **Description:** Document `claude mcp add` command for Claude Code per PRD §3.4
- **Priority:** P2
- **Dependencies:** P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Configuration snippet in docs
- **Acceptance Criteria:** Command `claude mcp add --transport stdio xcode -- /Users/$USER/bin/mcpbridge-wrapper` is documented

#### P6-T6: Create Codex CLI Configuration Template
- **Description:** Document `codex mcp add` command for Codex CLI per PRD §3.4
- **Priority:** P2
- **Dependencies:** P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Configuration snippet in docs
- **Acceptance Criteria:** Command `codex mcp add xcode -- /Users/$USER/bin/mcpbridge-wrapper` is documented

#### P6-T7: Configure pip Installable Package
- **Description:** Ensure `pip install` creates executable entry point
- **Priority:** P2
- **Dependencies:** P1-T2, P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `[project.scripts]` entry in pyproject.toml
- **Acceptance Criteria:** After `pip install`, `mcpbridge-wrapper` command is available in PATH

#### P6-T8: Create GitHub Release Workflow
- **Description:** GitHub Actions workflow to create releases with attached artifacts
- **Priority:** P3
- **Dependencies:** P1-T8, P6-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `.github/workflows/release.yml`
- **Acceptance Criteria:** Pushing tag creates release with downloadable script

---

### Phase 7: Documentation

#### P7-T1: Write Installation Guide Section
- **Description:** Document step-by-step installation for end users per PRD §4.1
- **Priority:** P0
- **Dependencies:** P6-T3
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `docs/installation.md` or README section
- **Acceptance Criteria:** New user can follow instructions without external help

#### P7-T2: Write Cursor Configuration Guide
- **Description:** Document GUI and JSON configuration for Cursor per PRD §4.1
- **Priority:** P0
- **Dependencies:** P6-T4
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/cursor-setup.md`
- **Acceptance Criteria:** Cursor successfully loads xcode-tools after following guide

#### P7-T3: Write Claude Code Configuration Guide
- **Description:** Document one-liner setup for Claude Code
- **Priority:** P1
- **Dependencies:** P6-T5
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/claude-setup.md` or combined doc
- **Acceptance Criteria:** `claude mcp list` shows xcode-tools after setup

#### P7-T4: Write Codex CLI Configuration Guide
- **Description:** Document one-liner setup for Codex CLI
- **Priority:** P1
- **Dependencies:** P6-T6
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/codex-setup.md` or combined doc
- **Acceptance Criteria:** `codex mcp list` shows xcode-tools after setup

#### P7-T5: Document Environment Variables
- **Description:** Document `MCP_XCODE_PID` and `MCP_XCODE_SESSION_ID` per PRD §6.2
- **Priority:** P1
- **Dependencies:** P2-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Environment variables table in documentation
- **Acceptance Criteria:** User understands when and how to use optional environment variables

#### P7-T6: Write Troubleshooting Guide
- **Description:** Document common errors and solutions per PRD §4.3
- **Priority:** P1
- **Dependencies:** P4-T1 through P4-T9
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/troubleshooting.md` covering -32600 error and others
- **Acceptance Criteria:** Each error has symptom, cause, and solution clearly documented

#### P7-T7: Document the 20 Xcode MCP Tools
- **Description:** List and briefly describe all available tools per PRD tool list
- **Priority:** P2
- **Dependencies:** P5-T13
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Tool reference table in documentation
- **Acceptance Criteria:** All 20 tools documented with name and description

#### P7-T8: Write Architecture Overview
- **Description:** Document how the wrapper works internally for contributors
- **Priority:** P2
- **Dependencies:** P3-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `docs/architecture.md` with diagrams
- **Acceptance Criteria:** Reader understands data flow from stdin to stdout

#### P7-T9: Create Usage Examples
- **Description:** Document sample workflows (build, test, read file)
- **Priority:** P2
- **Dependencies:** P5-T13
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - Example commands in documentation
- **Acceptance Criteria:** 3+ practical examples with expected output

#### P7-T10: Write Final README
- **Description:** Complete README with all essential information
- **Priority:** P0
- **Dependencies:** P7-T1, P7-T2, P7-T6
- **Parallelizable:** no
- **Outputs/Artifacts:** 
  - `README.md` at project root
- **Acceptance Criteria:** README includes: what, why, install, configure, usage, troubleshoot

#### P7-T11: Create CHANGELOG
- **Description:** Document version history and changes
- **Priority:** P2
- **Dependencies:** P7-T10
- **Parallelizable:** yes
- **Outputs/Artifacts:** 
  - `CHANGELOG.md` with initial 1.0.0 entry
- **Acceptance Criteria:** Follows Keep a Changelog format; all phases summarized

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

Before starting implementation, verify:
- [ ] Xcode 26.3+ is available for testing (P5-T12)
- [ ] Python 3.7+ is installed
- [ ] Target `~/bin` directory is writable

During execution:
- [ ] P5-T12 (real Xcode test) should be run early to validate assumptions
- [ ] P5-T11 (performance) must pass before Phase 6
- [ ] All P0 tasks must complete before considering MVP complete

Completion criteria:
- [ ] All P0 tasks: 100% complete
- [ ] All P1 tasks: ≥80% complete
- [ ] P5-T14 coverage: ≥90%
- [ ] P5-T13: All 20 tools verified
- [ ] P5-T11: <5ms overhead verified
