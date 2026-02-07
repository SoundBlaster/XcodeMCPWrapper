#!/usr/bin/env python3
"""CLI entry point for mcpbridge-wrapper."""

import sys


def main() -> int:
    """Main entry point for the mcpbridge-wrapper command."""
    print("mcpbridge-wrapper v1.0.0", file=sys.stderr)
    print("Use: mcpbridge-wrapper [args...]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
