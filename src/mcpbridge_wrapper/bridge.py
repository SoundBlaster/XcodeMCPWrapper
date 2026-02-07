"""Subprocess bridge to xcrun mcpbridge."""

import subprocess
import sys
import threading
from typing import Generator, List, Optional


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


def read_stdout(bridge: subprocess.Popen) -> Generator[str, None, None]:
    """
    Generator that yields complete lines from bridge stdout.

    This function provides a memory-efficient way to process bridge output
    line-by-line. It uses line buffering (bufsize=1) already configured
    in the subprocess.Popen call to ensure complete lines are yielded.

    Args:
        bridge: The Popen bridge process with readable stdout

    Yields:
        Complete lines from stdout (each ends with newline, except possibly last)

    Example:
        >>> bridge = create_bridge()
        >>> for line in read_stdout(bridge):
        ...     print(line, end='')
    """
    if bridge.stdout is None:
        return

    # Use iter with sentinel to read until EOF
    # Empty string from readline indicates EOF
    yield from iter(bridge.stdout.readline, "")


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


def run_stdin_forwarder(bridge: subprocess.Popen) -> threading.Thread:
    """
    Start a daemon thread that forwards stdin to bridge stdin.

    This function creates and starts a background thread that continuously
    reads lines from sys.stdin and forwards them to the bridge process.
    The thread runs as a daemon and will terminate when the main program exits.

    Args:
        bridge: The Popen bridge process with writable stdin

    Returns:
        The Thread object (daemon thread)

    Example:
        >>> bridge = create_bridge()
        >>> forwarder_thread = run_stdin_forwarder(bridge)
        >>> # Stdin is now being forwarded in the background
    """

    def forward_loop() -> None:
        """Inner loop that reads from stdin and forwards to bridge."""
        try:
            for line in sys.stdin:
                if bridge.stdin is not None:
                    bridge.stdin.write(line)
                    bridge.stdin.flush()
        except (BrokenPipeError, OSError):
            # Bridge stdin was closed, exit gracefully
            pass

    thread = threading.Thread(target=forward_loop, daemon=True)
    thread.start()
    return thread
