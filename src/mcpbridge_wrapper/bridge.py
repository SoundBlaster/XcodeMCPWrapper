"""Subprocess bridge to xcrun mcpbridge."""

import subprocess
import sys
from typing import List, Optional


def create_bridge(args: Optional[List[str]] = None) -> subprocess.Popen:
    """
    Create a subprocess bridge to xcrun mcpbridge.

    This function launches `xcrun mcpbridge` as a subprocess with bidirectional
    stdin/stdout pipes for MCP protocol communication.

    Args:
        args: Additional arguments to pass to mcpbridge (defaults to empty list)

    Returns:
        Popen object with readable stdout and writable stdin

    Example:
        >>> bridge = create_bridge()
        >>> bridge = create_bridge(["--help"])
    """
    if args is None:
        args = []

    cmd = ["xcrun", "mcpbridge"] + args

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1,
    )


def forward_stdin(bridge: subprocess.Popen, line: str) -> None:
    """
    Forward a line of input to the bridge's stdin.

    Args:
        bridge: The Popen bridge process
        line: Line to forward (should include newline)
    """
    if bridge.stdin is not None:
        bridge.stdin.write(line)
        bridge.stdin.flush()


def read_stdout_line(bridge: subprocess.Popen) -> Optional[str]:
    """
    Read a single line from the bridge's stdout.

    Args:
        bridge: The Popen bridge process

    Returns:
        Line from stdout, or None if EOF reached
    """
    if bridge.stdout is not None:
        return str(bridge.stdout.readline())
    return None


def cleanup_bridge(bridge: subprocess.Popen) -> int:
    """
    Clean up the bridge process and return its exit code.

    Args:
        bridge: The Popen bridge process

    Returns:
        Exit code of the bridge process
    """
    bridge.stdin.close() if bridge.stdin else None
    bridge.wait()
    return bridge.returncode
