#!/usr/bin/env python3
"""
CLI entry point for mcpbridge-wrapper.

This module provides the main entry point for the mcpbridge-wrapper command,
which wraps xcrun mcpbridge and adds structuredContent to MCP responses.
"""

import sys

from mcpbridge_wrapper.__main__ import main


def cli_main() -> int:
    """Main entry point for the mcpbridge-wrapper command."""
    return main()


if __name__ == "__main__":
    sys.exit(cli_main())
