# Product Requirements Document: mcpbridge-wrapper

## 1. Scope and Intent

### 1.1 Objective
Create a Python-based protocol compatibility wrapper (`mcpbridge-wrapper`) that intercepts MCP (Model Context Protocol) responses from Xcode 26.3's `xcrun mcpbridge` and transforms non-compliant responses into MCP-spec-compliant format by injecting the required `structuredContent` field.

### 1.2 Primary Deliverables
| ID | Deliverable | Description |
|----|-------------|-------------|
| D1 | `mcpbridge-wrapper` script | Executable Python 3 script that wraps `xcrun mcpbridge` |
| D2 | Installation documentation | Step-by-step setup guide for Cursor and other MCP clients |
| D3 | Configuration examples | JSON configs for various MCP client integrations |

### 1.3 Success Criteria
| ID | Criterion | Measurement |
|----|-----------|-------------|
| S1 | Cursor compatibility | All 20 Xcode MCP tools work in Cursor without `-32600` errors |
| S2 | Transparency | Zero functional difference between wrapper and native bridge |
| S3 | Performance | Response latency overhead < 5ms per request |
| S4 | Reliability | 100% success rate for valid JSON responses from mcpbridge |

### 1.4 Constraints and Dependencies
| Constraint | Description |
|------------|-------------|
| C1 | Requires Xcode 26.3+ with MCP bridge enabled |
| C2 | Requires Python 3.7+ (standard macOS installation) |
| C3 | Xcode must be running with project open for tools to function |
| C4 | Depends on `xcrun mcpbridge` binary from Xcode Command Line Tools |

---

## 2. Structured TODO Plan

### Phase 1: Core Wrapper Implementation
| ID | Task | Priority | Effort | Input | Output | Dependencies |
|----|------|----------|--------|-------|--------|--------------|
| T1.1 | Create subprocess bridge to `xcrun mcpbridge` | High | 1h | `mcpbridge` path | Bidirectional pipe | None |
| T1.2 | Implement stdin forwarding | High | 1h | MCP client requests | Forwarded to bridge | T1.1 |
| T1.3 | Implement stdout interception and processing | High | 2h | Bridge responses | Processed responses | T1.1 |
| T1.4 | Add JSON response transformation logic | High | 2h | Raw JSON responses | MCP-compliant JSON | T1.3 |
| T1.5 | Handle non-JSON output passthrough | Medium | 30m | Plain text lines | Unmodified output | T1.3 |
| T1.6 | Add threading for async stdout reading | High | 1h | Blocking stdout | Non-blocking pipe | T1.3 |

### Phase 2: Response Processing Logic
| ID | Task | Priority | Effort | Input | Output | Dependencies |
|----|------|----------|--------|-------|--------|--------------|
| T2.1 | Detect responses with `content` but no `structuredContent` | High | 1h | Parsed JSON | Boolean detection | T1.4 |
| T2.2 | Extract text content from `content` array | High | 1h | JSON object | Text string | T2.1 |
| T2.3 | Parse text as JSON for `structuredContent` | High | 1h | Text content | JSON object or fallback | T2.2 |
| T2.4 | Handle JSON decode errors with fallback wrapper | Medium | 30m | Invalid JSON | `{"text": content}` | T2.3 |
| T2.5 | Inject `structuredContent` into result object | High | 30m | Modified result | Compliant response | T2.3, T2.4 |

### Phase 3: Packaging and Distribution
| ID | Task | Priority | Effort | Input | Output | Dependencies |
|----|------|----------|--------|-------|--------|--------------|
| T3.1 | Add executable shebang and permissions | High | 15m | Script file | Executable script | T1.1-T2.5 |
| T3.2 | Create installation script for `~/bin` | Medium | 30m | Script location | Installed binary | T3.1 |
| T3.3 | Write Cursor MCP configuration | High | 30m | Wrapper path | Valid mcp.json | T3.1 |
| T3.4 | Test with all 20 Xcode MCP tools | High | 2h | Configuration | Test results | All above |

### Phase 4: Documentation
| ID | Task | Priority | Effort | Input | Output | Dependencies |
|----|------|----------|--------|-------|--------|--------------|
| T4.1 | Document installation steps | High | 1h | Implementation | README section | T3.1-T3.3 |
| T4.2 | Document configuration for Cursor | High | 30m | Cursor settings | Setup guide | T3.3 |
| T4.3 | Document troubleshooting | Medium | 30m | Common errors | FAQ section | T3.4 |
| T4.4 | Document environment variables | Low | 15m | Code analysis | Reference table | T1.1 |

### Parallel Execution Opportunities
- T1.1-T1.2 (subprocess setup) can be developed in parallel with T1.5 (passthrough logic)
- T4.1-T4.4 (documentation) can proceed in parallel with T3.4 (testing)

---

## 3. PRD: Feature Specifications

### 3.1 Feature: MCP Protocol Compliance Transformation

#### Description
The wrapper acts as a transparent intermediary that receives MCP responses from `xcrun mcpbridge`, detects non-compliant responses missing `structuredContent`, and injects the required field by transforming the existing `content` array data.

#### Rationale
- Xcode 26.3 RC's `mcpbridge` returns tool responses in `content` but omits `structuredContent`
- MCP specification requires `structuredContent` when `outputSchema` is declared
- Cursor strictly enforces MCP spec compliance, rejecting non-compliant responses
- Claude Code and Codex CLI work due to special-case handling for Apple

#### Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR1 | Intercept all stdout from `xcrun mcpbridge` | P0 | Every line from bridge is processed before reaching client |
| FR2 | Forward stdin to `xcrun mcpbridge` unmodified | P0 | Client requests reach bridge without alteration |
| FR3 | Parse JSON responses from bridge | P0 | Valid JSON is successfully parsed and validated |
| FR4 | Detect missing `structuredContent` in result objects | P0 | Correctly identifies responses with `content` but no `structuredContent` |
| FR5 | Extract text from `content` array items with `type: "text"` | P0 | First text item's content is extracted |
| FR6 | Parse extracted text as JSON for `structuredContent` | P0 | Valid JSON text becomes structuredContent object |
| FR7 | Fallback to `{"text": content}` on JSON decode error | P1 | Invalid JSON text is wrapped, not discarded |
| FR8 | Passthrough non-JSON output unchanged | P1 | Logs, errors, and plain text pass through unmodified |
| FR9 | Use unbuffered output for real-time responses | P0 | `flush=True` on all output operations |
| FR10 | Handle concurrent bidirectional I/O | P0 | Separate thread for stdout processing |

#### Non-Functional Requirements

| ID | Requirement | Target | Verification |
|----|-------------|--------|------------|
| NFR1 | Response latency overhead | < 5ms | Time 1000 requests, average < 5ms added |
| NFR2 | Memory footprint | < 10MB | Monitor process RSS during operation |
| NFR3 | CPU usage | < 1% idle | No polling loops, event-driven only |
| NFR4 | Compatibility | Python 3.7+ | Test on macOS default Python versions |
| NFR5 | Reliability | 99.9% uptime | No crashes during normal operation |
| NFR6 | Thread safety | Thread-safe | Proper daemon thread handling |

---

## 4. User Interaction Flows

### 4.1 Installation Flow

```
User
  │
  ▼
Run installation command ─────────► Create ~/bin/mcpbridge-wrapper
  │                                      │
  ▼                                      ▼
Make executable ◄────────────────── chmod +x ~/bin/mcpbridge-wrapper
  │
  ▼
Edit ~/.cursor/mcp.json ─────────► Add xcode-tools server config
  │
  ▼
Restart Cursor ──────────────────► MCP tools available
```

### 4.2 Runtime Request/Response Flow

```
┌─────────────┐         ┌───────────────────┐         ┌────────────┐
│   Cursor    │ ──────► │ mcpbridge-wrapper │ ──────► │ mcpbridge  │
│   (Client)  │  stdin  │    (This PRD)     │  stdin  │  (Bridge)  │
└─────────────┘         └───────────────────┘         └────────────┘
                              │                             │
                              │                             │
                              │    ┌──────────────┐         │
                              │    │ Transform:   │ ◄───────┘
                              │    │ +structured  │  stdout
                              │    │ _content    │
                              │    └──────────────┘
                              │           │
                              ▼           ▼
┌─────────────┐         ┌───────────────────┐
│   Cursor    │ ◄────── │ mcpbridge-wrapper │
│   (Client)  │  stdout │    (This PRD)     │
└─────────────┘         └───────────────────┘
```

---

## 5. Edge Cases and Failure Scenarios

### 5.1 Error Handling Matrix

| Scenario | Handling | Expected Behavior |
|----------|----------|-------------------|
| Non-JSON output from bridge | Passthrough | Output reaches client unchanged |
| Empty `content` array | No modification | Response passes through |
| `content` with no text items | No modification | Response passes through |
| Invalid JSON in text content | Fallback to `{"text": ...}` | Wrapped text as structuredContent |
| `structuredContent` already present | No modification | Response passes through |
| Bridge process crashes | Propagate exit | Wrapper exits with same code |
| Client disconnects | Clean shutdown | Wrapper terminates gracefully |
| Malformed JSON from bridge | Passthrough | Line sent to client as-is |

### 5.2 Specific Edge Cases

#### EC1: Mixed Content Types
```json
{
  "content": [
    {"type": "image", "url": "..."},
    {"type": "text", "text": "{\"result\": true}"}
  ]
}
```
**Expected**: Extract first text item, parse as JSON, inject as `structuredContent`

#### EC2: Already Compliant Response
```json
{
  "content": [{"type": "text", "text": "..."}],
  "structuredContent": {"existing": true}
}
```
**Expected**: No modification, pass through unchanged

#### EC3: Non-Text Content Only
```json
{
  "content": [{"type": "image", "url": "..."}]
}
```
**Expected**: No text to extract, pass through unchanged

#### EC4: Nested JSON String
```json
{
  "content": [{"type": "text", "text": "\"plain string\""}]
}
```
**Expected**: Parse as valid JSON string, inject as `structuredContent`

---

## 6. Configuration Specification

### 6.1 Cursor MCP Configuration

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/${USER}/bin/mcpbridge-wrapper"
    }
  }
}
```

### 6.2 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MCP_XCODE_PID` | No | Manually specify Xcode process ID |
| `MCP_XCODE_SESSION_ID` | No | UUID for Xcode tool session |

---

## 7. Testing and Verification

### 7.1 Unit Test Cases

| ID | Test Case | Input | Expected Output |
|----|-----------|-------|-----------------|
| TC1 | Valid transformation | Response with content, no structuredContent | Injected structuredContent |
| TC2 | Already compliant | Response with both fields | Unmodified |
| TC3 | Non-JSON text | Text content not valid JSON | `{"text": "..."}` wrapper |
| TC4 | Non-JSON line | Plain text stdout | Unmodified passthrough |
| TC5 | Empty content | `{"content": []}` | Unmodified |
| TC6 | No result field | `{"id": 1}` | Unmodified |

### 7.2 Integration Test Cases

| ID | Test Case | Verification |
|----|-----------|--------------|
| IT1 | `XcodeListWindows` | Returns valid structured content |
| IT2 | `BuildProject` | Successful build with compliant response |
| IT3 | `RenderPreview` | Image data properly structured |
| IT4 | Error response | Error details in structuredContent |

---

## 8. Quality Enforcement Checklist

- [ ] No vague language (all requirements are testable)
- [ ] Every step has clear input/output specifications
- [ ] Dependencies explicitly stated for all tasks
- [ ] Terminology consistent throughout (MCP, mcpbridge, structuredContent)
- [ ] All 20 Xcode tools accounted for in testing
- [ ] Failure scenarios have explicit handling rules
- [ ] Performance targets are measurable
