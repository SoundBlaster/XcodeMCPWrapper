"""Thread-safe metrics collection for the XcodeMCPWrapper web dashboard.

Collects real-time metrics including request counts, latency, error rates,
and per-tool usage statistics. Uses a rolling window for time-series data
to bound memory usage.
"""

import threading
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Tuple


def categorize_error(code: Optional[int]) -> str:
    """Categorize a JSON-RPC error code into a severity bucket.

    Categories:
    - "protocol": Standard JSON-RPC errors (-32600 to -32699)
    - "timeout": Timeout indicator (-32001)
    - "tool": Tool execution errors (positive codes >= 1)
    - "unknown": All other codes or None

    Args:
        code: The JSON-RPC error code, or None.

    Returns:
        Category string: "protocol", "timeout", "tool", or "unknown".
    """
    if code is None:
        return "unknown"
    if -32699 <= code <= -32600:
        return "protocol"
    if code == -32001:
        return "timeout"
    if code >= 1:
        return "tool"
    return "unknown"


class MetricsCollector:
    """Thread-safe metrics collector for MCP tool call monitoring.

    Tracks request counts, latencies, error rates, and per-tool statistics
    with a configurable rolling window for time-series data.

    Args:
        window_seconds: Duration of the rolling window for time-series data.
        max_datapoints: Maximum number of data points to retain per metric.
    """

    def __init__(self, window_seconds: int = 3600, max_datapoints: int = 3600) -> None:
        """Initialize the metrics collector.

        Args:
            window_seconds: Rolling window duration in seconds.
            max_datapoints: Maximum data points retained per time-series.
        """
        self._lock = threading.Lock()
        self._window_seconds = window_seconds
        self._max_datapoints = max_datapoints

        # Counters
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._start_time: float = time.time()

        # Per-tool counters
        self._tool_counts: Dict[str, int] = {}
        self._tool_errors: Dict[str, int] = {}
        self._tool_latencies: Dict[str, List[float]] = {}

        # Time-series data: deque of (timestamp, value) tuples
        self._request_times: Deque[float] = deque(maxlen=max_datapoints)
        self._error_times: Deque[float] = deque(maxlen=max_datapoints)
        self._latency_series: Deque[Tuple[float, float]] = deque(maxlen=max_datapoints)

        # In-flight request tracking for latency
        self._in_flight: Dict[str, float] = {}

        # MCP client identification
        self._client_name: str = "unknown"
        self._client_version: str = "unknown"

        # Error breakdown by code
        self._error_counts_by_code: Dict[int, int] = {}

        # Param pattern tracking: tool_name -> {sorted_key_tuple -> count}
        self._param_patterns: Dict[str, Dict[Tuple[str, ...], int]] = {}

    def set_client_info(self, name: str, version: str) -> None:
        """Record the connected MCP client identity.

        Args:
            name: Client name from initialize handshake (e.g. "Cursor").
            version: Client version string (e.g. "1.2.3").
        """
        with self._lock:
            self._client_name = name
            self._client_version = version

    def record_request(self, tool_name: str, request_id: Optional[str] = None) -> None:
        """Record an incoming request for a tool.

        Args:
            tool_name: Name of the MCP tool being called.
            request_id: Optional request ID for latency tracking.
        """
        now = time.time()
        with self._lock:
            self._total_requests += 1
            self._tool_counts[tool_name] = self._tool_counts.get(tool_name, 0) + 1
            self._request_times.append(now)
            if request_id is not None:
                self._in_flight[request_id] = now

    def record_response(
        self,
        tool_name: str,
        request_id: Optional[str] = None,
        error: bool = False,
        latency_ms: Optional[float] = None,
        error_code: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a response for a tool call.

        Args:
            tool_name: Name of the MCP tool.
            request_id: Optional request ID to compute latency from record_request.
            error: Whether the response indicates an error.
            latency_ms: Explicit latency in milliseconds. If not provided and
                request_id was tracked, latency is computed automatically.
            error_code: JSON-RPC error code (if error=True).
            error_message: JSON-RPC error message (if error=True).
        """
        now = time.time()
        with self._lock:
            if error:
                self._total_errors += 1
                self._tool_errors[tool_name] = self._tool_errors.get(tool_name, 0) + 1
                self._error_times.append(now)
                if error_code is not None:
                    self._error_counts_by_code[error_code] = (
                        self._error_counts_by_code.get(error_code, 0) + 1
                    )

            # Remove from in-flight tracking and compute latency if needed
            if request_id is not None:
                start = self._in_flight.pop(request_id, None)
                if start is not None and latency_ms is None:
                    latency_ms = (now - start) * 1000.0

            if latency_ms is not None:
                if tool_name not in self._tool_latencies:
                    self._tool_latencies[tool_name] = []
                self._tool_latencies[tool_name].append(latency_ms)
                # Cap per-tool latency history
                if len(self._tool_latencies[tool_name]) > self._max_datapoints:
                    self._tool_latencies[tool_name] = self._tool_latencies[tool_name][
                        -self._max_datapoints :
                    ]
                self._latency_series.append((now, latency_ms))

    def record_error(self, tool_name: str) -> None:
        """Record an error for a tool call (convenience method).

        Args:
            tool_name: Name of the MCP tool.
        """
        self.record_response(tool_name, error=True)

    def _compute_rps(self, now: Optional[float] = None, window: float = 60.0) -> float:
        """Compute requests per second over a rolling window.

        Args:
            now: Current timestamp. Defaults to time.time().
            window: Window duration in seconds.

        Returns:
            Requests per second within the window.
        """
        if now is None:
            now = time.time()
        cutoff = now - window
        count = sum(1 for t in self._request_times if t >= cutoff)
        return count / window if window > 0 else 0.0

    def _compute_error_rate(self, now: Optional[float] = None, window: float = 60.0) -> float:
        """Compute error rate over a rolling window.

        Args:
            now: Current timestamp. Defaults to time.time().
            window: Window duration in seconds.

        Returns:
            Error rate (0.0 to 1.0) within the window.
        """
        if now is None:
            now = time.time()
        cutoff = now - window
        req_count = sum(1 for t in self._request_times if t >= cutoff)
        err_count = sum(1 for t in self._error_times if t >= cutoff)
        return err_count / req_count if req_count > 0 else 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics.

        Returns:
            Dictionary containing current metrics snapshot.
        """
        now = time.time()
        with self._lock:
            uptime = now - self._start_time

            # Per-tool latency stats
            tool_latency_stats: Dict[str, Dict[str, float]] = {}
            for tool, latencies in self._tool_latencies.items():
                if latencies:
                    sorted_lat = sorted(latencies)
                    n = len(sorted_lat)
                    tool_latency_stats[tool] = {
                        "avg_ms": sum(sorted_lat) / n,
                        "min_ms": sorted_lat[0],
                        "max_ms": sorted_lat[-1],
                        "p50_ms": sorted_lat[n // 2],
                        "p95_ms": sorted_lat[int(n * 0.95)] if n >= 20 else sorted_lat[-1],
                        "p99_ms": sorted_lat[int(n * 0.99)] if n >= 100 else sorted_lat[-1],
                        "count": n,
                    }

            return {
                "uptime_seconds": round(uptime, 1),
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "rps": round(self._compute_rps(now), 2),
                "error_rate": round(self._compute_error_rate(now), 4),
                "tool_counts": dict(self._tool_counts),
                "tool_errors": dict(self._tool_errors),
                "tool_latency": tool_latency_stats,
                "in_flight": len(self._in_flight),
                "client_name": self._client_name,
                "client_version": self._client_version,
                "error_counts_by_code": dict(self._error_counts_by_code),
            }

    def get_timeseries(self, seconds: int = 300) -> Dict[str, Any]:
        """Get time-series data for charting.

        Args:
            seconds: Number of seconds of history to return.

        Returns:
            Dictionary with timestamped request, error, and latency data.
        """
        now = time.time()
        cutoff = now - seconds
        with self._lock:
            requests = [t for t in self._request_times if t >= cutoff]
            errors = [t for t in self._error_times if t >= cutoff]
            latencies = [(t, v) for t, v in self._latency_series if t >= cutoff]
            return {
                "window_seconds": seconds,
                "requests": [{"t": round(t - now, 2), "v": 1} for t in requests],
                "errors": [{"t": round(t - now, 2), "v": 1} for t in errors],
                "latencies": [{"t": round(t - now, 2), "v": round(v, 2)} for t, v in latencies],
            }

    def record_param_keys(self, tool_name: str, param_keys: List[str]) -> None:
        """Record a parameter key signature for a tool call.

        Only key names are stored — argument values are never captured.

        Args:
            tool_name: Name of the MCP tool.
            param_keys: List of argument key names from the tool call.
        """
        signature: Tuple[str, ...] = tuple(sorted(param_keys))
        with self._lock:
            if tool_name not in self._param_patterns:
                self._param_patterns[tool_name] = {}
            self._param_patterns[tool_name][signature] = (
                self._param_patterns[tool_name].get(signature, 0) + 1
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
        with self._lock:
            patterns = self._param_patterns.get(tool_name, {})
            sorted_patterns = sorted(patterns.items(), key=lambda kv: kv[1], reverse=True)
            return [{"keys": list(sig), "count": cnt} for sig, cnt in sorted_patterns[:top_n]]

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._start_time = time.time()
            self._tool_counts.clear()
            self._tool_errors.clear()
            self._tool_latencies.clear()
            self._request_times.clear()
            self._error_times.clear()
            self._latency_series.clear()
            self._in_flight.clear()
            self._client_name = "unknown"
            self._client_version = "unknown"
            self._error_counts_by_code.clear()
            self._param_patterns.clear()
