"""Structured audit logging with rotation for MCP tool calls.

Provides persistent audit logging of all MCP tool calls with timestamps,
request/response data, and export capabilities. Supports log rotation
by file size to prevent unbounded disk usage.
"""

import csv
import io
import json
import os
import threading
import time
from typing import Any, Dict, List, Optional


class AuditLogger:
    """Structured audit logger with file rotation for MCP tool calls.

    Logs each MCP tool call as a structured JSON record with timestamp,
    tool name, request/response data, latency, and error status. Supports
    rotation by file size and maximum file count.

    Args:
        log_dir: Directory for audit log files.
        max_file_size_mb: Maximum size per log file in megabytes.
        max_files: Maximum number of rotated log files to retain.
    """

    def __init__(
        self,
        log_dir: str = "logs/audit",
        max_file_size_mb: float = 10.0,
        max_files: int = 10,
    ) -> None:
        """Initialize the audit logger.

        Args:
            log_dir: Directory path for audit log files.
            max_file_size_mb: Max size per log file in MB before rotation.
            max_files: Max number of rotated files to keep.
        """
        self._log_dir = log_dir
        self._max_file_bytes = int(max_file_size_mb * 1024 * 1024)
        self._max_files = max_files
        self._lock = threading.Lock()
        self._current_file: Optional[io.TextIOWrapper] = None
        self._current_path: Optional[str] = None
        self._entries: List[Dict[str, Any]] = []
        self._max_memory_entries = 10000
        self._enabled = True

        os.makedirs(self._log_dir, exist_ok=True)
        self._open_log_file()

    def _log_filename(self) -> str:
        """Generate a timestamped log filename.

        Returns:
            Log filename with timestamp prefix.
        """
        ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        return f"audit_{ts}.jsonl"

    def _open_log_file(self) -> None:
        """Open a new log file for writing."""
        if self._current_file is not None:
            self._current_file.close()
        self._current_path = os.path.join(self._log_dir, self._log_filename())
        # File remains open for continuous logging; closed in close() method
        self._current_file = open(  # noqa: SIM115
            self._current_path, "a", encoding="utf-8"
        )

    def _rotate_if_needed(self) -> None:
        """Rotate log file if current file exceeds size limit."""
        if self._current_file is None or self._current_path is None:
            self._open_log_file()
            return

        try:
            size = os.path.getsize(self._current_path)
        except OSError:
            size = 0

        if size >= self._max_file_bytes:
            self._current_file.close()
            self._cleanup_old_files()
            self._open_log_file()

    def _cleanup_old_files(self) -> None:
        """Remove oldest log files exceeding max_files count."""
        try:
            files = sorted(
                [
                    f
                    for f in os.listdir(self._log_dir)
                    if f.startswith("audit_") and f.endswith(".jsonl")
                ]
            )
            while len(files) >= self._max_files:
                oldest = files.pop(0)
                os.remove(os.path.join(self._log_dir, oldest))
        except OSError:
            pass

    def log(
        self,
        tool_name: str,
        request_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
        direction: str = "request",
    ) -> None:
        """Log an audit entry for an MCP tool call.

        Args:
            tool_name: Name of the MCP tool.
            request_id: JSON-RPC request ID.
            request_data: Request payload (sanitized).
            response_data: Response payload (sanitized).
            latency_ms: Request latency in milliseconds.
            error: Error message if the call failed.
            direction: Either 'request' or 'response'.
        """
        if not self._enabled:
            return

        entry = {
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tool": tool_name,
            "direction": direction,
        }
        if request_id is not None:
            entry["request_id"] = request_id
        if request_data is not None:
            entry["request"] = request_data
        if response_data is not None:
            entry["response"] = response_data
        if latency_ms is not None:
            entry["latency_ms"] = round(latency_ms, 2)
        if error is not None:
            entry["error"] = error

        with self._lock:
            # Write to file
            self._rotate_if_needed()
            if self._current_file is not None:
                self._current_file.write(json.dumps(entry, separators=(",", ":")) + "\n")
                self._current_file.flush()

            # Keep in memory for dashboard
            self._entries.append(entry)
            if len(self._entries) > self._max_memory_entries:
                self._entries = self._entries[-self._max_memory_entries :]

    def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        tool_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent audit log entries.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip (from most recent).
            tool_filter: If set, only return entries for this tool.

        Returns:
            List of audit log entries, most recent first.
        """
        with self._lock:
            entries = self._entries
            if tool_filter:
                entries = [e for e in entries if e.get("tool") == tool_filter]
            # Reverse for most-recent-first
            entries = list(reversed(entries))
            return entries[offset : offset + limit]

    def export_json(self, limit: Optional[int] = None) -> str:
        """Export audit logs as a JSON string.

        Args:
            limit: Maximum number of entries to export. None for all.

        Returns:
            JSON string of audit log entries.
        """
        with self._lock:
            entries = self._entries
            if limit is not None:
                entries = entries[-limit:]
            return json.dumps(entries, indent=2)

    def export_csv(self, limit: Optional[int] = None) -> str:
        """Export audit logs as CSV.

        Args:
            limit: Maximum number of entries to export. None for all.

        Returns:
            CSV string of audit log entries.
        """
        with self._lock:
            entries = self._entries
            if limit is not None:
                entries = entries[-limit:]

        if not entries:
            return ""

        output = io.StringIO()
        fieldnames = [
            "timestamp_iso",
            "tool",
            "direction",
            "request_id",
            "latency_ms",
            "error",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)
        return output.getvalue()

    def get_entry_count(self) -> int:
        """Get the total number of in-memory audit entries.

        Returns:
            Number of entries in memory.
        """
        with self._lock:
            return len(self._entries)

    def close(self) -> None:
        """Close the current log file and release resources."""
        with self._lock:
            if self._current_file is not None:
                self._current_file.close()
                self._current_file = None

    @property
    def enabled(self) -> bool:
        """Whether audit logging is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable audit logging."""
        self._enabled = value
