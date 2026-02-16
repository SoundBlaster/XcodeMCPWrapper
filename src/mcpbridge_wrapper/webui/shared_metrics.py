"""Shared metrics storage using SQLite for multi-process metrics collection.

Since Zed starts multiple wrapper processes, each with its own metrics instance,
we need a shared storage mechanism. SQLite provides thread-safe, process-safe
storage that all processes can write to and read from.
"""

import contextlib
import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, cast

# Default database location
DEFAULT_DB_PATH = Path.home() / ".cache" / "mcpbridge-wrapper" / "metrics.db"


class SharedMetricsStore:
    """Process-safe metrics storage using SQLite.

    All wrapper processes write to the same database, and the Web UI
    reads aggregated metrics from it.

    Args:
        db_path: Path to SQLite database file.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize the shared metrics store."""
        self._db_path = db_path or DEFAULT_DB_PATH
        self._local = threading.local()
        self._start_time: float = time.time()
        self._ensure_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            # Ensure directory exists
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn: sqlite3.Connection = sqlite3.connect(str(self._db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
        return cast(sqlite3.Connection, self._local.connection)

    def _ensure_db(self) -> None:
        """Create tables if they don't exist."""
        with self._transaction() as conn:
            # Requests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT,
                    tool_name TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    latency_ms REAL,
                    error BOOLEAN DEFAULT 0,
                    error_code INTEGER,
                    error_message TEXT
                )
            """)
            # Add error_code and error_message columns to existing databases
            for col, col_type in [("error_code", "INTEGER"), ("error_message", "TEXT")]:
                with contextlib.suppress(Exception):
                    conn.execute(f"ALTER TABLE requests ADD COLUMN {col} {col_type}")
            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_tool ON requests(tool_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_time ON requests(timestamp)
            """)
            # Client info table (single-row upsert)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS client_info (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    client_name TEXT,
                    client_version TEXT,
                    updated_at REAL
                )
            """)
            # Param patterns table: stores frequency of argument key combinations per tool
            conn.execute("""
                CREATE TABLE IF NOT EXISTS param_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    param_signature TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(tool_name, param_signature)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_param_patterns_tool
                ON param_patterns(tool_name)
            """)

    @contextmanager
    def _transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def record_request(self, tool_name: str, request_id: Optional[str] = None) -> None:
        """Record an incoming request.

        Args:
            tool_name: Name of the MCP tool.
            request_id: Optional request ID for matching with response.
        """
        with self._transaction() as conn:
            conn.execute(
                "INSERT INTO requests (request_id, tool_name, timestamp) VALUES (?, ?, ?)",
                (request_id, tool_name, time.time()),
            )

    def record_response(
        self,
        tool_name: str,
        request_id: Optional[str] = None,
        error: bool = False,
        latency_ms: Optional[float] = None,
        error_code: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a response (updates the request record with latency/error).

        Args:
            tool_name: Name of the MCP tool.
            request_id: Optional request ID to match with request.
            error: Whether the response was an error.
            latency_ms: Response latency in milliseconds.
            error_code: JSON-RPC error code (if error=True).
            error_message: JSON-RPC error message (if error=True).
        """
        with self._transaction() as conn:
            if request_id:
                # Find the most recent request with this ID and tool name
                row = conn.execute(
                    """SELECT id FROM requests
                       WHERE request_id = ? AND tool_name = ? AND latency_ms IS NULL
                       ORDER BY id DESC LIMIT 1""",
                    (request_id, tool_name),
                ).fetchone()
                if row:
                    # Update existing request record
                    conn.execute(
                        """UPDATE requests
                           SET latency_ms = ?, error = ?, error_code = ?, error_message = ?
                           WHERE id = ?""",
                        (latency_ms, error, error_code, error_message, row["id"]),
                    )
                else:
                    # Insert as new record if no matching request found
                    conn.execute(
                        """INSERT INTO requests
                           (request_id, tool_name, timestamp, latency_ms, error,
                            error_code, error_message)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            request_id,
                            tool_name,
                            time.time(),
                            latency_ms,
                            error,
                            error_code,
                            error_message,
                        ),
                    )
            else:
                # Insert as new record (no request_id matching)
                conn.execute(
                    """INSERT INTO requests
                       (tool_name, timestamp, latency_ms, error, error_code, error_message)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (tool_name, time.time(), latency_ms, error, error_code, error_message),
                )

    def set_client_info(self, name: str, version: str) -> None:
        """Record the connected MCP client identity (upserts single row).

        Args:
            name: Client name from initialize handshake (e.g. "Cursor").
            version: Client version string (e.g. "1.2.3").
        """
        with self._transaction() as conn:
            conn.execute(
                """INSERT INTO client_info (id, client_name, client_version, updated_at)
                   VALUES (1, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       client_name=excluded.client_name,
                       client_version=excluded.client_version,
                       updated_at=excluded.updated_at""",
                (name, version, time.time()),
            )

    def get_summary(self, window_seconds: int = 3600) -> Dict[str, Any]:
        """Get aggregated metrics summary.

        Args:
            window_seconds: Time window for metrics (default 1 hour).

        Returns:
            Dict with aggregated metrics.
        """
        cutoff = time.time() - window_seconds

        with self._transaction() as conn:
            # Total counts
            row = conn.execute(
                "SELECT COUNT(*) as total, SUM(error) as errors FROM requests WHERE timestamp > ?",
                (cutoff,),
            ).fetchone()
            total_requests = row["total"] or 0
            total_errors = row["errors"] or 0

            # Per-tool counts
            tool_counts = {}
            tool_errors = {}
            tool_latency = {}

            cursor = conn.execute(
                """SELECT tool_name,
                          COUNT(*) as count,
                          SUM(error) as errors,
                          AVG(latency_ms) as avg_latency,
                          MIN(latency_ms) as min_latency,
                          MAX(latency_ms) as max_latency
                   FROM requests
                   WHERE timestamp > ? AND latency_ms IS NOT NULL
                   GROUP BY tool_name""",
                (cutoff,),
            )

            for row in cursor:
                name = row["tool_name"]
                tool_counts[name] = row["count"]
                tool_errors[name] = row["errors"] or 0
                tool_latency[name] = {
                    "avg_ms": row["avg_latency"],
                    "min_ms": row["min_latency"],
                    "max_ms": row["max_latency"],
                    "p50_ms": row["avg_latency"],  # Simplified
                    "p95_ms": row["max_latency"],  # Simplified
                    "p99_ms": row["max_latency"],  # Simplified
                    "count": row["count"],
                }

            # RPS calculation (requests in last 60 seconds)
            minute_cutoff = time.time() - 60
            row = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE timestamp > ?", (minute_cutoff,)
            ).fetchone()
            rps = (row[0] or 0) / 60.0

            # Error breakdown by code
            error_counts_by_code: Dict[int, int] = {}
            err_cursor = conn.execute(
                """SELECT error_code, COUNT(*) as cnt FROM requests
                   WHERE timestamp > ? AND error = 1 AND error_code IS NOT NULL
                   GROUP BY error_code""",
                (cutoff,),
            )
            for err_row in err_cursor:
                error_counts_by_code[err_row["error_code"]] = err_row["cnt"]

            # Client identification
            client_row = conn.execute(
                "SELECT client_name, client_version FROM client_info WHERE id = 1"
            ).fetchone()
            client_name = (client_row["client_name"] if client_row else None) or "unknown"
            client_version = (client_row["client_version"] if client_row else None) or "unknown"

            return {
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "rps": round(rps, 2),
                "error_rate": total_errors / total_requests if total_requests > 0 else 0.0,
                "tool_counts": tool_counts,
                "tool_errors": tool_errors,
                "tool_latency": tool_latency,
                "in_flight": 0,  # Can't track across processes easily
                "client_name": client_name,
                "client_version": client_version,
                "error_counts_by_code": error_counts_by_code,
            }

    def get_timeseries(self, seconds: int = 300) -> Dict[str, List[Dict[str, Any]]]:
        """Get time-series data for charting.

        Returns data in format expected by frontend Chart.js:
        {
            "requests": [{"t": seconds_ago, "v": count}, ...],
            "errors": [{"t": seconds_ago, "v": count}, ...],
            "latencies": [{"t": seconds_ago, "v": latency_ms}, ...]
        }

        Args:
            seconds: Time window in seconds.

        Returns:
            Dict with time-series arrays.
        """
        cutoff = time.time() - seconds
        now = time.time()
        bucket_size = 5  # 5-second buckets to match frontend

        with self._transaction() as conn:
            # Query all records in time window
            cursor = conn.execute(
                """SELECT timestamp, error, latency_ms
                   FROM requests
                   WHERE timestamp > ?
                   ORDER BY timestamp""",
                (cutoff,),
            )

            # Bucket data by time (seconds ago, 5-second buckets)
            buckets: Dict[int, Dict[str, Any]] = {}

            for row in cursor:
                timestamp = row["timestamp"]
                seconds_ago = int((now - timestamp) / bucket_size) * bucket_size

                if seconds_ago not in buckets:
                    buckets[seconds_ago] = {
                        "requests": 0,
                        "errors": 0,
                        "latencies": [],
                    }

                buckets[seconds_ago]["requests"] += 1
                if row["error"]:
                    buckets[seconds_ago]["errors"] += 1
                if row["latency_ms"] is not None:
                    buckets[seconds_ago]["latencies"].append(row["latency_ms"])

            # Convert buckets to sorted arrays
            sorted_times = sorted(buckets.keys(), reverse=True)

            requests_data = []
            errors_data = []
            latencies_data = []

            for t in sorted_times:
                bucket = buckets[t]
                requests_data.append({"t": t, "v": bucket["requests"]})
                errors_data.append({"t": t, "v": bucket["errors"]})
                if bucket["latencies"]:
                    avg_latency = sum(bucket["latencies"]) / len(bucket["latencies"])
                    latencies_data.append({"t": t, "v": round(avg_latency, 2)})

            return {
                "requests": requests_data,
                "errors": errors_data,
                "latencies": latencies_data,
            }

    def record_param_keys(self, tool_name: str, param_keys: List[str]) -> None:
        """Record a parameter key signature for a tool call.

        Only key names are stored — argument values are never captured.

        Args:
            tool_name: Name of the MCP tool.
            param_keys: List of argument key names from the tool call.
        """
        signature = json.dumps(sorted(param_keys))
        with self._transaction() as conn:
            conn.execute(
                """INSERT INTO param_patterns (tool_name, param_signature, count)
                   VALUES (?, ?, 1)
                   ON CONFLICT(tool_name, param_signature)
                   DO UPDATE SET count = count + 1""",
                (tool_name, signature),
            )

    def get_param_patterns(self, tool_name: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Return the most common parameter key combinations for a tool.

        Args:
            tool_name: Name of the MCP tool to query.
            top_n: Maximum number of patterns to return.

        Returns:
            List of dicts with ``keys`` (sorted list) and ``count``, ordered
            by descending count.
        """
        with self._transaction() as conn:
            cursor = conn.execute(
                """SELECT param_signature, count
                   FROM param_patterns
                   WHERE tool_name = ?
                   ORDER BY count DESC
                   LIMIT ?""",
                (tool_name, top_n),
            )
            return [
                {"keys": json.loads(row["param_signature"]), "count": row["count"]}
                for row in cursor
            ]

    def reset(self) -> None:
        """Clear all metrics data."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM requests")
            conn.execute("DELETE FROM client_info")
            conn.execute("DELETE FROM param_patterns")

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
