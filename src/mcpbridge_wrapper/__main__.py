"""Entry point for mcpbridge-wrapper."""

import sys

from mcpbridge_wrapper.bridge import (
    cleanup_bridge,
    create_bridge,
    read_stdout_line,
    run_stdin_forwarder,
)


def main() -> int:
    """
    Main entry point for the mcpbridge-wrapper command.

    Creates a bridge to xcrun mcpbridge, starts stdin forwarding,
    and processes stdout responses.
    """
    # Create bridge with forwarded command-line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    bridge = create_bridge(args)

    # Start stdin forwarding in a daemon thread
    run_stdin_forwarder(bridge)

    # Process stdout from bridge and forward to our stdout
    exit_code = 0
    try:
        while True:
            line = read_stdout_line(bridge)
            if line is None or line == "":
                # EOF reached
                break
            sys.stdout.write(line)
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        exit_code = cleanup_bridge(bridge)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
