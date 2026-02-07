"""Entry point for mcpbridge-wrapper."""

import signal
import sys

from mcpbridge_wrapper.bridge import (
    cleanup_bridge,
    create_bridge,
    run_stdin_forwarder,
    run_stdout_reader,
)
from mcpbridge_wrapper.transform import process_response_line


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
    try:
        # Process lines from the queue until EOF (None sentinel)
        while True:
            line = output_queue.get()
            if line is None:
                # EOF reached - bridge closed stdout
                break

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

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
