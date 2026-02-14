# BUG-T7: Normalize `resources/*` Method Failures to Standard JSON-RPC Errors

**Task ID:** BUG-T7
**Type:** Bug / MCP Compatibility / Error Normalization
**Priority:** P0
**Status:** 🟡 In Progress
**Discovered:** 2026-02-14
**Component:** Response normalization — non-tool method error handling

---

## 1. Problem Statement

For unsupported methods like `resources/list` and `resources/templates/list`, the upstream
`xcrun mcpbridge` returns a **tool-style** `result.isError/content` payload:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "isError": true,
    "content": [{"type": "text", "text": "Method not found: resources/list"}]
  }
}
```

Strict MCP clients (Cursor, Codex) expect a **JSON-RPC error** envelope for failed non-tool
methods:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found: resources/list"
  }
}
```

This mismatch causes "Unexpected response type" errors in strict clients.

---

## 2. Root Cause

The wrapper's `transform.py` focuses exclusively on `structuredContent` injection for tool
results. It does not distinguish between:
- `tools/call` responses (where `isError: true` is a valid, passthrough result)
- Non-tool method responses (where `isError: true` should map to a JSON-RPC error)

Because there is no request/response correlation in the transformation layer, the wrapper
cannot determine which method the response belongs to.

---

## 3. Deliverables

### 3.1 New/Modified Files

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/transform.py` | Add `normalize_resources_error()`, `is_tool_call_result()`, update `process_response_line()` |
| `src/mcpbridge_wrapper/__main__.py` | Add `pending_methods` map; track method per request_id; pass method to `process_response_line()` |
| `tests/unit/test_transform.py` | Add `TestNormalizeResourcesError` test class |
| `tests/unit/test_main.py` | Add tests for method tracking and normalization in the main loop |

### 3.2 Core Logic

#### transform.py additions

```python
def is_tool_call_result(data: Any) -> bool:
    """Return True if data looks like a tools/call result (has result.content list)."""
    ...

def normalize_resources_error(data: dict) -> Optional[dict]:
    """
    If data is a non-tool isError result, return a JSON-RPC error envelope.
    Returns None if not applicable.
    """
    ...

def process_response_line(line: str, method: Optional[str] = None) -> str:
    """
    Existing function — adds optional `method` parameter.
    When method is provided and is NOT 'tools/call', and the response
    has result.isError=True, normalize to JSON-RPC error.
    """
    ...
```

#### __main__.py additions

```python
# Track request_id -> method for ALL incoming requests
pending_methods: Dict[str, str] = {}

# In on_request: for any request with id + method, record it
# In response loop: look up method, pass to process_response_line
```

---

## 4. Acceptance Criteria

- [ ] `resources/list` with `result.isError=true` upstream → `error: {code: -32601, message: ...}` output
- [ ] `resources/templates/list` with `result.isError=true` → same normalization
- [ ] `tools/call` with `result.isError=true` → **unchanged** (tool errors are valid passthrough)
- [ ] `tools/call` with `result.isError=false` → `structuredContent` injection still works
- [ ] Responses with `id: null` (notifications) → pass through unchanged
- [ ] All existing 323+ unit tests still pass
- [ ] New tests cover all 4 normalization scenarios above
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes

---

## 5. Error Code Rationale

Use `-32601` (Method Not Found) as the default error code for unsupported methods. This aligns
with the JSON-RPC 2.0 spec. If the upstream content text starts with a parseable error message,
use it verbatim as the `message` field.

---

## 6. Backward Compatibility

- `process_response_line(line)` (no method arg) continues to work identically for all existing callers
- Tool call behavior is completely unchanged
- Only non-tool method `isError` responses are normalized

---

## 7. Dependencies

- P3-T10: Main response processing loop (implemented ✅)
- BUG-T6: Port collision fix (implemented ✅)

---

## 8. Test Cases

| ID | Scenario | Input | Expected Output |
|----|----------|-------|-----------------|
| TC1 | resources/list isError | `{"jsonrpc":"2.0","id":1,"result":{"isError":true,"content":[{"type":"text","text":"not found"}]}}` with method=`resources/list` | `{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"not found"}}` |
| TC2 | tools/call isError passthrough | same structure with method=`tools/call` | **unchanged** |
| TC3 | tools/call success | `{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"{}"}]}}` | `structuredContent` injected |
| TC4 | No method provided | resources-style isError, method=None | **unchanged** (conservative fallback) |
| TC5 | Response with no id | notification | **unchanged** |
| TC6 | resources/templates/list isError | same as TC1 for different method | same normalization |
| TC7 | isError in content missing | `{"result":{"isError":true,"content":[]}}` with non-tool method | `{"error":{"code":-32601,"message":"Method not supported"}}` |
