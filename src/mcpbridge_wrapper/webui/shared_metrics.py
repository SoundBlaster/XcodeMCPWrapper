"""Shared metrics storage using SQLite for multi-process metrics collection.

Since Zed starts multiple wrapper processes, each with its own metrics instance,
we need a shared storage mechanism. SQLite provides thread-safe, process-safe
storage that all processes can write to and read from.
"""

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
                    error BOOLEAN DEFAULT 0
                )
            """)
            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_tool ON requests(tool_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_time ON requests(timestamp)
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
    ) -> None:
        """Record a response (updates the request record with latency/error).

        Args:
            tool_name: Name of the MCP tool.
            request_id: Optional request ID to match with request.
            error: Whether the response was an error.
            latency_ms: Response latency in milliseconds.
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
                        "UPDATE requests SET latency_ms = ?, error = ? WHERE id = ?",
                        (latency_ms, error, row["id"]),
                    )
                else:
                    # Insert as new record if no matching request found
                    conn.execute(
                        """INSERT INTO requests
                           (request_id, tool_name, timestamp, latency_ms, error)
                           VALUES (?, ?, ?, ?, ?)""",
                        (request_id, tool_name, time.time(), latency_ms, error),
                    )
            else:
                # Insert as new record (no request_id matching)
                conn.execute(
                    """INSERT INTO requests
                       (tool_name, timestamp, latency_ms, error) VALUES (?, ?, ?, ?)""",
                    (tool_name, time.time(), latency_ms, error),
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

            return {
                "uptime_seconds": window_seconds,  # Approximate
                "total_requests": total_requests,
                "total_errors": total_errors,
                "rps": round(rps, 2),
                "error_rate": total_errors / total_requests if total_requests > 0 else 0.0,
                "tool_counts": tool_counts,
                "tool_errors": tool_errors,
                "tool_latency": tool_latency,
                "in_flight": 0,  # Can't track across processes easily
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

    def reset(self) -> None:
        """Clear all metrics data."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM requests")

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
