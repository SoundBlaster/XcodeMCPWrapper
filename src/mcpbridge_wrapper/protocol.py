"""MCP 2026-07-28 protocol boundary used by every public frontend.

The Xcode subprocess is an implementation detail.  Clients connecting to this
package always speak the stateless MCP 2026-07-28 wire contract: every request
 carries its protocol version and client capabilities in ``params._meta``.
"""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from mcp import types as mcp_types

try:
    _PACKAGE_VERSION = version("mcpbridge-wrapper")
except PackageNotFoundError:  # pragma: no cover - installed package is the runtime path.
    _PACKAGE_VERSION = "0.0.0+unknown"

PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_PROTOCOL_VERSIONS = (PROTOCOL_VERSION,)
PROTOCOL_VERSION_META = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_META = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_META = "io.modelcontextprotocol/clientInfo"
SERVER_INFO_META = "io.modelcontextprotocol/serverInfo"
SUBSCRIPTION_ID_META = "io.modelcontextprotocol/subscriptionId"

ERROR_INVALID_PARAMS = -32602
ERROR_METHOD_NOT_FOUND = -32601
ERROR_MISSING_CLIENT_CAPABILITY = -32021
ERROR_UNSUPPORTED_PROTOCOL_VERSION = -32022

# These are the capabilities implemented by the wrapper boundary.  The Xcode
# catalog is still discovered at runtime; advertising the transport contract
# here must not depend on a previous request on the same connection.
SERVER_CAPABILITIES: dict[str, Any] = {
    "tools": {"listChanged": True},
    "resources": {"listChanged": True},
    "prompts": {"listChanged": True},
}


def _is_request_id(value: Any) -> bool:
    """Return whether *value* is a valid modern JSON-RPC request ID."""
    return isinstance(value, (str, int)) and not isinstance(value, bool)


def error_response(
    request_id: Any,
    code: int,
    message: str,
    *,
    data: Any | None = None,
) -> dict[str, Any]:
    """Build a JSON-RPC error response without losing the request ID."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def encode_message(message: dict[str, Any]) -> str:
    """Serialize one protocol message as a compact JSON line."""
    return json.dumps(message, separators=(",", ":"))


def request_meta(message: dict[str, Any]) -> dict[str, Any] | None:
    """Return the request ``params._meta`` object, if present and valid."""
    params = message.get("params")
    if not isinstance(params, dict):
        return None
    meta = params.get("_meta")
    return meta if isinstance(meta, dict) else None


def request_protocol_version(message: dict[str, Any]) -> str | None:
    """Return the per-request protocol revision."""
    meta = request_meta(message)
    version = meta.get(PROTOCOL_VERSION_META) if meta is not None else None
    return version if isinstance(version, str) else None


def validate_request(message: Any) -> dict[str, Any] | None:
    """Validate the public MCP request contract.

    ``None`` means valid.  The returned value is a JSON-RPC error response for
    the caller to send.  Notifications are accepted without request metadata,
    while every request must carry the version and capabilities fields required
    by the 2026-07-28 base protocol.
    """
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return error_response(None, -32600, "Invalid Request")

    method = message.get("method")
    if not isinstance(method, str) or not method:
        return error_response(message.get("id"), -32600, "Invalid Request")

    has_id = "id" in message
    request_id = message.get("id")
    if has_id and not _is_request_id(request_id):
        return error_response(None, -32600, "Request id must be a string or integer")

    # Legacy lifecycle methods are deliberately not part of the public 1.0 API.
    if method in {"initialize", "notifications/initialized"}:
        return (
            error_response(
                request_id if has_id else None,
                ERROR_METHOD_NOT_FOUND,
                f"{method} is not supported by MCP {PROTOCOL_VERSION}; use per-request _meta",
            )
            if has_id
            else None
        )

    if not has_id:
        return None

    meta = request_meta(message)
    if meta is None:
        return error_response(
            request_id,
            ERROR_INVALID_PARAMS,
            "params._meta is required for MCP 2026-07-28 requests",
        )

    version = meta.get(PROTOCOL_VERSION_META)
    if version not in SUPPORTED_PROTOCOL_VERSIONS:
        return error_response(
            request_id,
            ERROR_UNSUPPORTED_PROTOCOL_VERSION,
            "Unsupported MCP protocol version",
            data={
                "requestedVersion": version,
                "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
            },
        )

    capabilities = meta.get(CLIENT_CAPABILITIES_META)
    if not isinstance(capabilities, dict):
        return error_response(
            request_id,
            ERROR_INVALID_PARAMS,
            f"params._meta.{CLIENT_CAPABILITIES_META} is required and must be an object",
        )

    return None


def discovery_response(request_id: str | int) -> dict[str, Any]:
    """Return the wrapper's self-contained modern discovery response."""
    result = mcp_types.DiscoverResult.model_validate(
        {
            "resultType": "complete",
            "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
            "capabilities": SERVER_CAPABILITIES,
            "_meta": {SERVER_INFO_META: {"name": "mcpbridge-wrapper", "version": _PACKAGE_VERSION}},
            "ttlMs": 0,
            "cacheScope": "private",
        }
    )
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result.model_dump(by_alias=True, exclude_none=True),
    }


def modernize_response(
    message: dict[str, Any],
    *,
    method: str | None = None,
) -> dict[str, Any]:
    """Normalize an upstream result to the modern response envelope.

    This is deliberately conservative: valid structured output, MRTR fields,
    cache hints, and unknown extension fields are preserved.  Only fields that
    the modern base protocol requires or recommends are added when absent.
    """
    result = message.get("result")
    if not isinstance(result, dict):
        return message

    result.setdefault("resultType", "complete")
    if method in {
        "server/discover",
        "tools/list",
        "resources/list",
        "resources/templates/list",
        "prompts/list",
    }:
        result.setdefault("ttlMs", 0)
        result.setdefault("cacheScope", "private")
    meta = result.get("_meta")
    if not isinstance(meta, dict):
        meta = {}
        result["_meta"] = meta
    meta.setdefault(SERVER_INFO_META, {"name": "mcpbridge-wrapper", "version": _PACKAGE_VERSION})

    return message


def is_notification(message: dict[str, Any]) -> bool:
    """Return whether *message* is a JSON-RPC notification."""
    return "id" not in message
