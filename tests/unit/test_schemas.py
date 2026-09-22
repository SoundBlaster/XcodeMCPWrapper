"""Tests for modern MCP schema adapters."""

from __future__ import annotations

from mcpbridge_wrapper.schemas import MCPRequest, parse_mcp_message


def test_request_reads_client_info_from_modern_metadata() -> None:
    request = MCPRequest.model_validate(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {
                "_meta": {"io.modelcontextprotocol/clientInfo": {"name": "Cursor", "version": "1"}}
            },
        }
    )

    assert request.get_client_info().name == "Cursor"


def test_invalid_client_info_metadata_is_ignored() -> None:
    request = MCPRequest.model_validate(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {"_meta": {"io.modelcontextprotocol/clientInfo": {"name": 1}}},
        }
    )

    assert request.get_client_info() is None


def test_schema_client_info_fallbacks_are_explicit() -> None:
    direct = MCPRequest.model_validate(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {"clientInfo": {"name": "internal", "version": "1"}},
        }
    )
    without_params = MCPRequest.model_validate(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    )

    assert direct.get_client_info().name == "internal"
    assert without_params.get_client_info() is None


def test_parse_mcp_message_returns_none_for_invalid_json() -> None:
    assert parse_mcp_message("not json") is None
