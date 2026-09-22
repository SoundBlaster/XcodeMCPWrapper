"""Tests for the public MCP 2026-07-28 protocol boundary."""

from __future__ import annotations

from mcpbridge_wrapper.protocol import (
    ERROR_INVALID_PARAMS,
    ERROR_METHOD_NOT_FOUND,
    ERROR_UNSUPPORTED_PROTOCOL_VERSION,
    discovery_response,
    error_response,
    modernize_response,
    request_protocol_version,
    validate_request,
)


def _request(method: str = "tools/list") -> dict:
    return {
        "jsonrpc": "2.0",
        "id": "request-1",
        "method": method,
        "params": {
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                "io.modelcontextprotocol/clientCapabilities": {},
            }
        },
    }


def test_valid_request_uses_per_request_metadata() -> None:
    assert validate_request(_request()) is None


def test_missing_metadata_uses_invalid_params() -> None:
    message = _request()
    message["params"] = {}
    error = validate_request(message)
    assert error is not None
    assert error["error"]["code"] == ERROR_INVALID_PARAMS


def test_unknown_version_reports_supported_versions() -> None:
    message = _request()
    message["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "2025-11-25"
    error = validate_request(message)
    assert error is not None
    assert error["error"]["code"] == ERROR_UNSUPPORTED_PROTOCOL_VERSION
    assert error["error"]["data"]["supportedVersions"] == ["2026-07-28"]


def test_legacy_initialize_is_not_a_public_method() -> None:
    message = _request("initialize")
    error = validate_request(message)
    assert error is not None
    assert error["error"]["code"] == ERROR_METHOD_NOT_FOUND


def test_discovery_is_complete_and_cacheable() -> None:
    response = discovery_response("discover-1")
    result = response["result"]
    assert result["resultType"] == "complete"
    assert result["ttlMs"] == 0
    assert result["cacheScope"] == "private"


def test_modernize_preserves_mrtr_and_extension_fields() -> None:
    response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "inputRequests": {"profile": {"method": "elicitation/create"}},
            "requestState": "opaque-state",
            "vendor.example/trace": {"attempt": 1},
        },
    }
    modernize_response(response)
    assert response["result"]["resultType"] == "complete"
    assert response["result"]["requestState"] == "opaque-state"
    assert response["result"]["vendor.example/trace"] == {"attempt": 1}


def test_modernize_catalog_response_adds_private_cache_hints() -> None:
    response = {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}

    modernize_response(response, method="tools/list")

    assert response["result"]["ttlMs"] == 0
    assert response["result"]["cacheScope"] == "private"


def test_protocol_rejects_malformed_requests_and_missing_capabilities() -> None:
    assert validate_request([])["error"]["code"] == -32600
    assert validate_request({"jsonrpc": "2.0", "method": ""})["error"]["code"] == -32600
    invalid_id = _request()
    invalid_id["id"] = None
    assert validate_request(invalid_id)["error"]["code"] == -32600

    message = _request()
    message["params"]["_meta"].pop("io.modelcontextprotocol/clientCapabilities")
    error = validate_request(message)
    assert error is not None
    assert error["error"]["code"] == ERROR_INVALID_PARAMS


def test_notifications_and_metadata_helpers_are_stateless() -> None:
    notification = {"jsonrpc": "2.0", "method": "notifications/cancelled"}
    assert validate_request(notification) is None
    assert request_protocol_version(_request()) == "2026-07-28"
    assert request_protocol_version({"params": {}}) is None
    assert request_protocol_version({"params": "invalid"}) is None


def test_modernize_leaves_error_response_unchanged() -> None:
    response = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601}}
    assert modernize_response(response) is response

    result_with_invalid_meta = {"jsonrpc": "2.0", "id": 2, "result": {"_meta": 1}}
    modernize_response(result_with_invalid_meta)
    assert isinstance(result_with_invalid_meta["result"]["_meta"], dict)


def test_error_response_keeps_structured_error_data() -> None:
    response = error_response(1, -32602, "bad", data={"field": "name"})
    assert response["error"]["data"] == {"field": "name"}
