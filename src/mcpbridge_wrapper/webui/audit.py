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
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple


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

    _MAX_PAYLOAD_BYTES = 64 * 1024  # 64 KB per payload
    _MAX_PAYLOAD_ENTRIES = 500  # ring buffer capacity

    def __init__(
        self,
        log_dir: str = "logs/audit",
        max_file_size_mb: float = 10.0,
        max_files: int = 10,
        capture_payload: bool = False,
    ) -> None:
        """Initialize the audit logger.

        Args:
            log_dir: Directory path for audit log files.
            max_file_size_mb: Max size per log file in MB before rotation.
            max_files: Max number of rotated files to keep.
            capture_payload: Whether to store full request/response payloads.
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
        self._capture_payload = capture_payload
        self._history_signature: Tuple[Tuple[str, int, int], ...] = ()
        # OrderedDict preserves insertion order; oldest entry evicted when full.
        self._payload_buffer: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        os.makedirs(self._log_dir, exist_ok=True)
        self._open_log_file()
        self._load_history()

    def _log_files_snapshot(self) -> Tuple[Tuple[str, int, int], ...]:
        """Return sorted audit log file metadata used for change detection.

        Each tuple entry is ``(filename, size_bytes, mtime_ns)``. Any change in
        this snapshot means on-disk history changed and should be reloaded.
        """
        try:
            snapshot: List[Tuple[str, int, int]] = []
            for filename in os.listdir(self._log_dir):
                if not (filename.startswith("audit_") and filename.endswith(".jsonl")):
                    continue
                path = os.path.join(self._log_dir, filename)
                try:
                    stat = os.stat(path)
                except OSError:
                    continue
                mtime_ns = int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)))
                snapshot.append((filename, int(stat.st_size), mtime_ns))
            snapshot.sort(key=lambda item: item[0])
            return tuple(snapshot)
        except OSError:
            return ()

    def _load_history(self, force: bool = False) -> None:
        """Load or refresh existing JSONL entries from ``log_dir``.

        Reads all ``audit_*.jsonl`` files in chronological order and populates
        ``self._entries`` with the most-recent ``_max_memory_entries`` entries.
        Malformed lines are silently skipped. Reloading is skipped unless file
        metadata changes (or ``force=True``), which keeps reads cheap while
        preserving visibility into entries written by sibling processes.
        """
        snapshot = self._log_files_snapshot()
        if not force and snapshot == self._history_signature:
            return

        raw_lines: List[str] = []
        for filename, _size, _mtime_ns in snapshot:
            path = os.path.join(self._log_dir, filename)
            try:
                with open(path, encoding="utf-8") as fh:
                    raw_lines.extend(fh.readlines())
            except OSError:
                continue

        # Keep only the most-recent N lines before parsing (cheap truncation).
        if len(raw_lines) > self._max_memory_entries:
            raw_lines = raw_lines[-self._max_memory_entries :]

        entries: List[Dict[str, Any]] = []
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict):
                    entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue

        self._entries = entries
        self._history_signature = snapshot

    def _update_history_signature_after_local_write(self) -> None:
        """Advance cached history signature after this process appends a log.

        This avoids triggering a full history reload on the next read endpoint
        call when only local writes happened since the previous signature.
        """
        if self._current_path is None:
            return

        # Start from known entries that still exist.
        signature_map: Dict[str, Tuple[int, int]] = {}
        for filename, size, mtime_ns in self._history_signature:
            path = os.path.join(self._log_dir, filename)
            if os.path.exists(path):
                signature_map[filename] = (size, mtime_ns)

        try:
            stat = os.stat(self._current_path)
        except OSError:
            self._history_signature = tuple(
                sorted(
                    (filename, size, mtime_ns)
                    for filename, (size, mtime_ns) in signature_map.items()
                )
            )
            return

        filename = os.path.basename(self._current_path)
        mtime_ns = int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)))
        signature_map[filename] = (int(stat.st_size), mtime_ns)
        self._history_signature = tuple(
            sorted((name, size, mtime) for name, (size, mtime) in signature_map.items())
        )

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

    @staticmethod
    def _truncate_payload(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Serialise *data* to JSON and truncate to _MAX_PAYLOAD_BYTES if needed.

        Returns the original dict when it fits within the limit, or a
        ``{"_truncated": true, "raw": "<truncated JSON>"}`` dict otherwise.

        Args:
            data: The payload dict to check.

        Returns:
            Original dict, truncated wrapper, or None when data is None.
        """
        if data is None:
            return None
        serialised = json.dumps(data, separators=(",", ":"))
        encoded = serialised.encode("utf-8")
        if len(encoded) <= AuditLogger._MAX_PAYLOAD_BYTES:
            return data
        truncated = encoded[: AuditLogger._MAX_PAYLOAD_BYTES].decode("utf-8", errors="replace")
        return {"_truncated": True, "raw": truncated}

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
            # Best-effort cleanup: ignore filesystem errors so audit logging continues.
            pass

    def log(
        self,
        tool_name: str,
        request_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
        error_code: Optional[int] = None,
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
            error_code: JSON-RPC error code if the call failed.
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
        if error_code is not None:
            entry["error_code"] = error_code

        with self._lock:
            # Write to file
            self._rotate_if_needed()
            if self._current_file is not None:
                self._current_file.write(json.dumps(entry, separators=(",", ":")) + "\n")
                self._current_file.flush()
                self._update_history_signature_after_local_write()

            # Keep in memory for dashboard
            self._entries.append(entry)
            if len(self._entries) > self._max_memory_entries:
                self._entries = self._entries[-self._max_memory_entries :]

            # Store payload in ring buffer when capture is enabled
            if self._capture_payload and request_id is not None:
                payload_entry: Dict[str, Any] = {
                    "request": self._truncate_payload(request_data),
                    "response": self._truncate_payload(response_data),
                }
                self._payload_buffer[request_id] = payload_entry
                # Evict oldest entries when buffer is full
                while len(self._payload_buffer) > self._MAX_PAYLOAD_ENTRIES:
                    self._payload_buffer.popitem(last=False)

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
            self._load_history()
            entries = list(self._entries)
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
            self._load_history()
            entries = list(self._entries)
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
            self._load_history()
            entries = list(self._entries)
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
            "error_code",
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
            self._load_history()
            return len(self._entries)

    def get_payload(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Return the stored request/response payload for *request_id*.

        Args:
            request_id: The JSON-RPC request ID to look up.

        Returns:
            Dict with ``request`` and ``response`` keys, or ``None`` when the
            ID is not in the ring buffer or payload capture is disabled.
        """
        if not self._capture_payload:
            return None
        with self._lock:
            return self._payload_buffer.get(request_id)

    @property
    def capture_payload(self) -> bool:
        """Whether payload capture is enabled."""
        return self._capture_payload

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
