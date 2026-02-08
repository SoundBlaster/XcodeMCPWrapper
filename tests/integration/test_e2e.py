"""
End-to-end integration tests for mcpbridge-wrapper.

These tests use a mock bridge process to verify the full
stdin→transform→stdout cycle without requiring actual Xcode.
"""

import json
import subprocess
import sys
import time
from typing import Any

import pytest


class MockBridge:
    """A mock mcpbridge that outputs canned responses."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.input_lines: list[str] = []

    def run(self) -> None:
        """Run the mock bridge, reading stdin and writing responses."""
        for line in sys.stdin:
            self.input_lines.append(line.strip())

        for response in self.responses:
            print(response, flush=True)


@pytest.fixture
def mock_bridge_script(tmp_path):
    """Create a temporary mock bridge script."""
    script = tmp_path / "mock_bridge.py"
    script.write_text('''
import sys
import json

# Read all input
for line in sys.stdin:
    pass

# Output canned responses
responses = [
    '{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "{\\"status\\": \\"ok\\"}"]}}',
    '{"jsonrpc": "2.0", "id": 2, "result": {"content": [], "structuredContent": {}}}',
    'Plain text log message',
    '{"jsonrpc": "2.0", "id": 3, "error": {"code": -32600, "message": "Invalid Request"}}',
]

for resp in responses:
    print(resp, flush=True)
''')
    return str(script)


class TestEndToEnd:
    """End-to-end tests using mock bridge."""

    def test_full_cycle_with_mock_bridge(self, tmp_path):
        """Test complete stdin→transform→stdout cycle."""
        # Create a mock bridge that outputs a response needing transformation
        mock_bridge = tmp_path / "mock_bridge.py"
        mock_bridge.write_text('''
import sys
for line in sys.stdin:
    pass
print('{"result": {"content": [{"type": "text", "text": "{\\"buildResult\\": \\"success\\"}"]}}', flush=True)
''')

        # Run the wrapper with the mock bridge
        env = {
            **dict(subprocess.os.environ),
            "PYTHONPATH": str(tmp_path),
        }

        proc = subprocess.Popen(
            [sys.executable, "-m", "mcpbridge_wrapper"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Send a request
        request = '{"jsonrpc": "2.0", "id": 1, "method": "test"}\n'
        stdout, stderr = proc.communicate(input=request, timeout=5)

        # Verify the response was transformed
        lines = stdout.strip().split('\n')
        response = json.loads(lines[0])
        
        assert "result" in response
        assert "structuredContent" in response["result"]
        assert response["result"]["structuredContent"]["buildResult"] == "success"

    def test_non_json_passthrough(self, tmp_path):
        """Test that non-JSON lines pass through unchanged."""
        mock_bridge = tmp_path / "mock_bridge.py"
        mock_bridge.write_text('''
import sys
for line in sys.stdin:
    pass
print('Log: Processing request', flush=True)
print('{"result": {"content": []}}', flush=True)
''')

        proc = subprocess.Popen(
            [sys.executable, "-m", "mcpbridge_wrapper"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        request = '{"jsonrpc": "2.0", "id": 1}\n'
        stdout, _ = proc.communicate(input=request, timeout=5)

        lines = stdout.strip().split('\n')
        assert lines[0] == "Log: Processing request"
        
        response = json.loads(lines[1])
        assert "result" in response

    def test_already_compliant_response(self, tmp_path):
        """Test that already compliant responses are not modified."""
        mock_bridge = tmp_path / "mock_bridge.py"
        mock_bridge.write_text('''
import sys
for line in sys.stdin:
    pass
print('{"result": {"content": [], "structuredContent": {"already": "present"}}}', flush=True)
''')

        proc = subprocess.Popen(
            [sys.executable, "-m", "mcpbridge_wrapper"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        request = '{"jsonrpc": "2.0", "id": 1}\n'
        stdout, _ = proc.communicate(input=request, timeout=5)

        response = json.loads(stdout.strip())
        assert response["result"]["structuredContent"] == {"already": "present"}


class TestMockBridgeFixture:
    """Tests using the mock bridge fixture."""

    def test_mock_bridge_outputs_expected_responses(self, tmp_path):
        """Verify our mock bridge produces expected output."""
        mock_bridge = tmp_path / "mock_bridge.py"
        mock_bridge.write_text('''
import sys
for line in sys.stdin:
    pass
print('{"result": {"content": [{"type": "text", "text": "test"}]}}', flush=True)
''')

        proc = subprocess.Popen(
            [sys.executable, str(mock_bridge)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, _ = proc.communicate(input='request\n', timeout=5)
        response = json.loads(stdout.strip())
        
        assert response["result"]["content"][0]["text"] == "test"
