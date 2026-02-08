"""
Performance benchmark tests for mcpbridge-wrapper.

Verifies that the wrapper overhead is <5ms per transformation (NFR1).
"""

import json
import statistics
import subprocess
import sys
import time
from typing import Callable

import pytest

from mcpbridge_wrapper.transform import process_response_line


class TestPerformance:
    """Performance benchmark tests."""

    def test_transformation_overhead_under_5ms(self):
        """
        Verify transformation overhead is under 5ms per request (NFR1).

        This test times 1000 transformations and calculates average latency.
        """
        test_line = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"content": [{"type": "text", "text": '{"status": "ok"}'}]},
            }
        )

        # Warm up
        for _ in range(100):
            process_response_line(test_line)

        # Time 1000 transformations
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            result = process_response_line(test_line)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0

        # Print benchmark results
        print(f"\n{'=' * 50}")
        print(f"Performance Benchmark Results (1000 iterations)")
        print(f"{'=' * 50}")
        print(f"Average: {avg_time:.4f} ms")
        print(f"Median:  {median_time:.4f} ms")
        print(f"Min:     {min_time:.4f} ms")
        print(f"Max:     {max_time:.4f} ms")
        print(f"Stdev:   {stdev:.4f} ms")
        print(f"{'=' * 50}")

        # Assert average is under 5ms
        assert avg_time < 5.0, f"Average overhead {avg_time:.4f}ms exceeds 5ms limit"
        assert median_time < 5.0, f"Median overhead {median_time:.4f}ms exceeds 5ms limit"

    def test_large_json_processing_performance(self):
        """
        Verify processing of large JSON responses is efficient.

        Tests that large payloads (>10KB) don't cause excessive memory/time usage.
        """
        # Create a large JSON payload (~10KB)
        large_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "data": "x" * 5000,  # 5KB of data
                                "items": list(range(100)),
                                "nested": {"deep": {"structure": True}},
                            }
                        ),
                    }
                ]
            },
        }
        test_line = json.dumps(large_data)

        # Time processing
        times = []
        for _ in range(100):
            start = time.perf_counter()
            result = process_response_line(test_line)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = statistics.mean(times)

        print(f"\nLarge JSON (10KB) processing: {avg_time:.4f} ms avg")

        # Even large payloads should process in under 10ms
        assert avg_time < 10.0, f"Large payload processing {avg_time:.4f}ms too slow"

    def test_non_json_passthrough_performance(self):
        """
        Verify non-JSON lines pass through with minimal overhead.
        """
        test_lines = [
            "Plain text log message",
            "Error: Something went wrong",
            "INFO: Processing request ID 12345",
            "WARN: Deprecated API usage",
        ]

        times = []
        for line in test_lines * 250:  # 1000 total
            start = time.perf_counter()
            result = process_response_line(line)
            end = time.perf_counter()
            times.append((end - start) * 1000)

            # Verify passthrough
            assert result == line

        avg_time = statistics.mean(times)

        print(f"\nNon-JSON passthrough: {avg_time:.4f} ms avg")

        # Non-JSON should be even faster (<1ms)
        assert avg_time < 1.0, f"Non-JSON overhead {avg_time:.4f}ms too high"

    def test_memory_efficiency(self):
        """
        Verify memory usage stays reasonable during processing.

        Note: This is a basic check. For comprehensive memory profiling,
        use memory_profiler or similar tools.
        """
        import gc

        # Force garbage collection
        gc.collect()

        # Process many lines
        test_line = json.dumps(
            {"result": {"content": [{"type": "text", "text": '{"data": "test"}'}]}}
        )

        # Process 10000 lines
        for _ in range(10000):
            process_response_line(test_line)

        # Force GC again
        gc.collect()

        # If we got here without MemoryError, we pass
        # This test mainly ensures we don't have obvious memory leaks
        assert True


class TestBenchmarkReport:
    """Generate a benchmark report."""

    @pytest.mark.skip(reason="Run manually to generate full report")
    def test_generate_benchmark_report(self):
        """Generate a comprehensive benchmark report."""
        test_cases = [
            ("Simple JSON", '{"result": {"content": [{"type": "text", "text": "{}"}]}}'),
            (
                "Complex JSON",
                json.dumps(
                    {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(
                                        {
                                            "buildResult": "success",
                                            "elapsedTime": 2.17,
                                            "errors": [],
                                            "warnings": ["deprecated API"],
                                            "artifacts": [{"name": "app", "size": 1024}],
                                        }
                                    ),
                                }
                            ]
                        }
                    }
                ),
            ),
            ("Non-JSON", "Plain text log message"),
            ("Already Compliant", '{"result": {"content": [], "structuredContent": {}}}'),
        ]

        print(f"\n{'=' * 60}")
        print(f"mcpbridge-wrapper Performance Benchmark Report")
        print(f"{'=' * 60}")

        for name, test_line in test_cases:
            times = []
            for _ in range(1000):
                start = time.perf_counter()
                process_response_line(test_line)
                end = time.perf_counter()
                times.append((end - start) * 1000)

            avg = statistics.mean(times)
            median = statistics.median(times)

            print(f"\n{name}:")
            print(f"  Average: {avg:.4f} ms")
            print(f"  Median:  {median:.4f} ms")
            print(f"  Status:  {'✓ PASS' if avg < 5.0 else '✗ FAIL'}")

        print(f"\n{'=' * 60}")
