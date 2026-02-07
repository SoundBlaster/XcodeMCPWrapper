"""
Unit tests for the transform module.
"""

import pytest

from mcpbridge_wrapper.transform import is_json_line


class TestIsJsonLine:
    """Tests for is_json_line function."""

    def test_valid_json_object(self) -> None:
        """Should return True for valid JSON object."""
        assert is_json_line('{"key": "value"}') is True

    def test_valid_json_array(self) -> None:
        """Should return True for valid JSON array."""
        assert is_json_line('[1, 2, 3]') is True

    def test_valid_json_string_primitive(self) -> None:
        """Should return True for JSON string primitive."""
        assert is_json_line('"plain string"') is True

    def test_valid_json_number_primitive(self) -> None:
        """Should return True for JSON number primitive."""
        assert is_json_line('42') is True

    def test_valid_json_boolean_true(self) -> None:
        """Should return True for JSON boolean true."""
        assert is_json_line('true') is True

    def test_valid_json_boolean_false(self) -> None:
        """Should return True for JSON boolean false."""
        assert is_json_line('false') is True

    def test_valid_json_null(self) -> None:
        """Should return True for JSON null."""
        assert is_json_line('null') is True

    def test_plain_text_rejection(self) -> None:
        """Should return False for plain text log."""
        assert is_json_line('Plain text log') is False

    def test_plain_text_with_colon(self) -> None:
        """Should return False for plain text with colon."""
        assert is_json_line('Error: something went wrong') is False

    def test_partial_json_rejection(self) -> None:
        """Should return False for partial/broken JSON."""
        assert is_json_line('{"broken') is False

    def test_empty_string(self) -> None:
        """Should return False for empty string."""
        assert is_json_line('') is False

    def test_whitespace_only(self) -> None:
        """Should return False for whitespace-only string."""
        assert is_json_line('   ') is False

    def test_nested_json_object(self) -> None:
        """Should return True for nested JSON object."""
        assert is_json_line('{"outer": {"inner": "value"}}') is True

    def test_json_with_special_characters(self) -> None:
        """Should return True for JSON with special characters."""
        assert is_json_line('{"text": "Hello\\nWorld"}') is True

    def test_json_array_of_objects(self) -> None:
        """Should return True for JSON array of objects."""
        assert is_json_line('[{"id": 1}, {"id": 2}]') is True
