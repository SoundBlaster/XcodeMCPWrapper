"""Subprocess bridge to xcrun mcpbridge."""

import contextlib
import os
import queue
import subprocess
import sys
import threading
from typing import Any, Callable, Generator, List, Optional, Tuple


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

    Note:
        For testing, set MCP_BRIDGE_CMD environment variable to override the
        bridge command. Format: "executable,arg1,arg2,..." (comma-separated)
    """
    if args is None:
        args = []

    # Check for environment variable override (for testing)
    bridge_cmd = os.environ.get("MCP_BRIDGE_CMD")
    cmd = bridge_cmd.split(",") + args if bridge_cmd else ["xcrun", "mcpbridge"] + args

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


def verify_bridge_started(bridge: subprocess.Popen) -> bool:
    """
    Verify that the bridge process started successfully.

    This function checks if the bridge process is still running after
    creation. It uses poll() which returns None if the process is running.

    Args:
        bridge: The Popen bridge process

    Returns:
        True if process is running, False if it failed to start

    Example:
        >>> bridge = create_bridge()
        >>> if verify_bridge_started(bridge):
        ...     print("Bridge started successfully")
        ... else:
        ...     print("Bridge failed to start")
    """
    # poll() returns None if process is still running
    return bridge.poll() is None


def cleanup_bridge(bridge: subprocess.Popen, timeout: Optional[float] = None) -> int:
    """
    Clean up the bridge process and return its exit code.

    This function performs a clean shutdown of the bridge process:
    1. Closes stdin to signal EOF to the bridge
    2. Waits for the process to terminate
    3. Returns the exit code

    Args:
        bridge: The Popen bridge process
        timeout: Optional timeout in seconds to wait for termination.
                 If None, waits indefinitely. If specified and process
                 doesn't terminate in time, it's terminated forcefully.

    Returns:
        Exit code of the bridge process

    Example:
        >>> bridge = create_bridge()
        >>> # ... use bridge ...
        >>> exit_code = cleanup_bridge(bridge)
        >>> print(f"Bridge exited with code {exit_code}")
    """
    # Close stdin to signal EOF to the bridge
    if bridge.stdin is not None:
        with contextlib.suppress(BrokenPipeError, OSError):
            bridge.stdin.close()

    # Wait for process to terminate
    try:
        if timeout is not None:
            bridge.wait(timeout=timeout)
        else:
            bridge.wait()
    except subprocess.TimeoutExpired:
        # Force terminate if timeout expired
        bridge.terminate()
        try:
            bridge.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            bridge.kill()
            bridge.wait()

    return bridge.returncode


def run_stdin_forwarder(
    bridge: subprocess.Popen,
    metrics: Optional[Any] = None,
    audit: Optional[Any] = None,
    on_request: Optional[callable] = None,
) -> threading.Thread:
    """
    Start a daemon thread that forwards stdin to bridge stdin.

    This function creates and starts a background thread that continuously
    reads lines from sys.stdin and forwards them to the bridge process.
    The thread runs as a daemon and will terminate when the main program exits.

    Args:
        bridge: The Popen bridge process with writable stdin
        metrics: Optional metrics collector for tracking requests
        audit: Optional audit logger for logging requests
        on_request: Optional callback(line) called for each request line

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
                # Track request metrics if enabled
                if on_request is not None:
                    try:
                        on_request(line)
                    except Exception:
                        pass  # Don't break forwarding on metric errors

                if bridge.stdin is not None:
                    bridge.stdin.write(line)
                    bridge.stdin.flush()
        except (BrokenPipeError, OSError):
            # Bridge stdin was closed, exit gracefully
            pass

    thread = threading.Thread(target=forward_loop, daemon=True)
    thread.start()
    return thread


def run_stdout_reader(bridge: subprocess.Popen) -> Tuple[threading.Thread, queue.Queue]:
    """
    Start a daemon thread that reads bridge stdout into a queue.

    This function creates and starts a background thread that continuously
    reads lines from the bridge's stdout and places them into a thread-safe
    queue. The main thread can then consume lines from the queue without
    blocking on I/O operations.

    The thread runs as a daemon and will terminate when the main program exits.
    When the bridge closes its stdout (EOF), the thread puts a None sentinel
    into the queue and exits.

    Args:
        bridge: The Popen bridge process with readable stdout

    Returns:
        Tuple of (thread, queue) where queue contains lines from stdout.
        A None sentinel is placed in the queue when EOF is reached.

    Example:
        >>> bridge = create_bridge()
        >>> thread, output_queue = run_stdout_reader(bridge)
        >>> # Main thread can now process from queue without blocking
        >>> line = output_queue.get(timeout=1.0)
    """
    output_queue: queue.Queue = queue.Queue()

    def reader_loop() -> None:
        """Inner loop that reads from bridge stdout and puts to queue."""
        try:
            if bridge.stdout is not None:
                for line in iter(bridge.stdout.readline, ""):
                    output_queue.put(line)
            # Put None sentinel to indicate EOF
            output_queue.put(None)
        except (BrokenPipeError, OSError, ValueError):
            # Bridge stdout was closed or queue operation failed
            output_queue.put(None)

    thread = threading.Thread(target=reader_loop, daemon=True)
    thread.start()
    return thread, output_queue
