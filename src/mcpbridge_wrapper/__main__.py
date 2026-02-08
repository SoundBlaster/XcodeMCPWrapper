"""Entry point for mcpbridge-wrapper."""

import signal
import sys
import time

from mcpbridge_wrapper.bridge import (
    cleanup_bridge,
    create_bridge,
    run_stdin_forwarder,
    run_stdout_reader,
)
from mcpbridge_wrapper.transform import process_response_line

# Diagnostic tracking
_seen_initialize = False
_seen_tools_request = False
_tools_response_timeout = False

def check_xcode_tools_enabled() -> None:
    """Print diagnostic message if Xcode Tools MCP is likely not enabled."""
    print(
        "\n⚠️  DIAGNOSTIC: Xcode Tools MCP service is not responding.\n"
        "   This usually means Xcode Tools MCP is not enabled in Xcode settings.\n\n"
        "   To fix this:\n"
        "   1. Open Xcode > Settings (⌘,)\n"
        "   2. Select 'Intelligence' in the sidebar\n"
        "   3. Under 'Model Context Protocol', toggle 'Xcode Tools' ON\n\n"
        "   Then restart Cursor/Zed/Claude and try again.\n",
        file=sys.stderr,
    )


def main() -> int:
    """
    Main entry point for the mcpbridge-wrapper command.

    Creates a bridge to xcrun mcpbridge, starts stdin forwarding in a daemon
    thread, reads stdout via a daemon thread into a queue, processes each
    response line through process_response_line() for MCP compliance transformation,
    and outputs unbuffered results to stdout.

    Returns:
        Exit code from the bridge process (0 for success)
    """
    # Create bridge with forwarded command-line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    bridge = create_bridge(args)

    # Verify bridge started successfully
    if bridge.poll() is not None:
        print("Error: Failed to start mcpbridge", file=sys.stderr)
        return 1

    # Start stdin forwarding in a daemon thread
    _ = run_stdin_forwarder(bridge)  # Thread runs in background, no direct reference needed

    # Start stdout reader in a daemon thread with queue
    stdout_thread, output_queue = run_stdout_reader(bridge)

    # Set up signal handlers for clean shutdown
    def signal_handler(signum: int, frame: object) -> None:
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        pass  # Let the main loop handle cleanup via queue

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    exit_code = 0
    global _seen_initialize, _seen_tools_request
    
    try:
        # Process lines from the queue until EOF (None sentinel)
        while True:
            line = output_queue.get()
            if line is None:
                # EOF reached - bridge closed stdout
                break

            # Track initialization for diagnostics
            if '"method":"initialize"' in line.replace(' ', '') or '"method": "initialize"' in line:
                _seen_initialize = True
            if '"method":"tools/list"' in line.replace(' ', '') or '"method": "tools/list"' in line:
                _seen_tools_request = True

            # Transform the response line for MCP compliance
            processed = process_response_line(line)

            # Output unbuffered (flush=True via write + flush)
            sys.stdout.write(processed)
            # Ensure newline if line doesn't end with one
            if processed and not processed.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        # User interrupted - clean shutdown will proceed in finally block
        pass
    finally:
        # Clean up bridge and get exit code
        exit_code = cleanup_bridge(bridge)
        
        # Diagnostic: if we saw initialize and tools/list but bridge exited cleanly (0)
        # without responding to tools/list, Xcode Tools MCP is likely not enabled
        if _seen_initialize and _seen_tools_request and exit_code == 0:
            check_xcode_tools_enabled()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
