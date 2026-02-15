"""JSON Schema definitions for MCP (Model Context Protocol) messages.

This module provides Pydantic models for validating and parsing MCP protocol
messages. Using strong typing ensures we correctly handle the protocol format.
"""

from typing import Any, Dict, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover
    # If pydantic isn't installed, stop importing this module entirely.
    # The wrapper requires pydantic at runtime, and this avoids mypy
    # issues with conditional redefinitions.
    raise


class MCPClientInfo(BaseModel):
    """MCP client identification from initialize handshake.

    Attributes:
        name: Client name (e.g., "Cursor", "Claude")
        version: Client version (e.g., "1.2.3")
    """

    model_config = {"extra": "allow"}

    name: str = Field(default="unknown", description="Client name")
    version: str = Field(default="unknown", description="Client version")


class MCPInitializeParams(BaseModel):
    """MCP initialize request parameters.

    Attributes:
        clientInfo: Optional client identification
    """

    model_config = {"extra": "allow"}

    clientInfo: Optional[MCPClientInfo] = Field(default=None, description="Client info")  # noqa: N815


class MCPParams(BaseModel):
    """MCP tool call parameters.

    Attributes:
        name: The tool name (e.g., "BuildProject", "XcodeRead")
        arguments: Optional tool arguments
        clientInfo: Optional client identification (present in initialize requests)
    """

    model_config = {"extra": "allow"}

    name: Optional[str] = Field(default=None, description="Tool name")
    arguments: Optional[Dict[str, Any]] = Field(default=None, description="Tool arguments")
    clientInfo: Optional[MCPClientInfo] = Field(  # noqa: N815
        default=None, description="Client info (initialize)"
    )


class MCPRequest(BaseModel):
    """MCP JSON-RPC request message.

    Attributes:
        jsonrpc: Protocol version (always "2.0")
        id: Request ID (can be string, int, or null)
        method: JSON-RPC method (e.g., "tools/call", "initialize")
        params: Method parameters containing tool name
    """

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Optional[Any] = Field(default=None, description="Request ID")
    method: Optional[str] = Field(default=None, description="JSON-RPC method")
    params: Optional[MCPParams] = Field(default=None, description="Method parameters")

    def get_tool_name(self) -> Optional[str]:
        """Extract the tool name from the request.

        For tools/call format: returns params.name
        For direct tool calls: returns method (if not a protocol method)

        Returns:
            Tool name if found, None otherwise
        """
        # Check for MCP tools/call format
        if self.method == "tools/call" and self.params and self.params.name:
            # Filter out protocol methods
            if self.params.name in ("initialize", "tools/list"):
                return None
            return self.params.name

        # Check for direct tool call (non-protocol method)
        if self.method and not self.method.startswith("tools/"):
            return self.method

        return None

    def get_client_info(self) -> Optional["MCPClientInfo"]:
        """Extract client info from an initialize request.

        Returns:
            MCPClientInfo if method is "initialize" and clientInfo is present,
            None otherwise.
        """
        if self.method != "initialize":
            return None
        if self.params is not None and self.params.clientInfo is not None:
            return self.params.clientInfo
        return None


class MCPResponseResult(BaseModel):
    """MCP response result container.

    Attributes:
        name: Tool name in result
        toolName: Alternative tool name field
        content: Response content
        structuredContent: Structured response content
    """

    name: Optional[str] = Field(default=None, description="Tool name")
    toolName: Optional[str] = Field(default=None, description="Alternative tool name field")  # noqa: N815
    content: Optional[Any] = Field(default=None, description="Response content")
    structuredContent: Optional[Any] = Field(default=None, description="Structured content")  # noqa: N815


class MCPError(BaseModel):
    """MCP JSON-RPC error.

    Attributes:
        code: Error code
        message: Error message
        data: Optional error data
    """

    code: int = Field(description="Error code")
    message: str = Field(description="Error message")
    data: Optional[Any] = Field(default=None, description="Error data")


class MCPResponse(BaseModel):
    """MCP JSON-RPC response message.

    Attributes:
        jsonrpc: Protocol version
        id: Response ID (matches request ID)
        result: Response result
        error: Error if the call failed
    """

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Optional[Any] = Field(default=None, description="Response ID")
    result: Optional[MCPResponseResult] = Field(default=None, description="Response result")
    error: Optional[MCPError] = Field(default=None, description="Error if failed")

    def get_tool_name(self) -> Optional[str]:
        """Extract the tool name from the response.

        Returns:
            Tool name from result.name or result.toolName if found
        """
        if self.result:
            return self.result.name or self.result.toolName
        return None

    def has_error(self) -> bool:
        """Check if the response contains an error.

        Returns:
            True if error field is present
        """
        return self.error is not None

    def get_error_code(self) -> Optional[int]:
        """Return the JSON-RPC error code, or None if no error.

        Returns:
            Error code integer, or None if no error present
        """
        return self.error.code if self.error is not None else None

    def get_error_message(self) -> Optional[str]:
        """Return the JSON-RPC error message, or None if no error.

        Returns:
            Error message string, or None if no error present
        """
        return self.error.message if self.error is not None else None


def parse_mcp_message(line: str) -> Optional[MCPRequest]:
    """Parse an MCP message from a JSON line.

    Args:
        line: JSON line from MCP bridge

    Returns:
        Parsed MCPRequest if valid, None otherwise
    """
    try:
        return MCPRequest.model_validate_json(line)
    except Exception:  # pragma: no cover
        return None
