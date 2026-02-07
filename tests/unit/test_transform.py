"""
Unit tests for the transform module.
"""

import pytest

from mcpbridge_wrapper.transform import is_json_line, needs_transformation, parse_json_safe


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


class TestParseJsonSafe:
    """Tests for parse_json_safe function."""

    def test_valid_json_object_returns_success(self) -> None:
        """Should return (True, parsed_dict) for valid JSON object."""
        success, result = parse_json_safe('{"key": "value"}')
        assert success is True
        assert result == {"key": "value"}

    def test_valid_json_array_returns_success(self) -> None:
        """Should return (True, parsed_list) for valid JSON array."""
        success, result = parse_json_safe('[1, 2, 3]')
        assert success is True
        assert result == [1, 2, 3]

    def test_valid_json_string_primitive(self) -> None:
        """Should return (True, string) for JSON string primitive."""
        success, result = parse_json_safe('"plain string"')
        assert success is True
        assert result == "plain string"

    def test_valid_json_number_primitive(self) -> None:
        """Should return (True, number) for JSON number primitive."""
        success, result = parse_json_safe('42')
        assert success is True
        assert result == 42

    def test_valid_json_boolean(self) -> None:
        """Should return (True, bool) for JSON boolean."""
        success, result = parse_json_safe('true')
        assert success is True
        assert result is True

    def test_valid_json_null(self) -> None:
        """Should return (True, None) for JSON null."""
        success, result = parse_json_safe('null')
        assert success is True
        assert result is None

    def test_invalid_json_returns_failure_with_original(self) -> None:
        """Should return (False, original_line) for invalid JSON."""
        original = 'invalid json'
        success, result = parse_json_safe(original)
        assert success is False
        assert result == original

    def test_partial_json_returns_failure(self) -> None:
        """Should return (False, original) for partial JSON."""
        original = '{"broken'
        success, result = parse_json_safe(original)
        assert success is False
        assert result == original

    def test_empty_string_returns_failure(self) -> None:
        """Should return (False, original) for empty string."""
        original = ''
        success, result = parse_json_safe(original)
        assert success is False
        assert result == original

    def test_whitespace_only_returns_failure(self) -> None:
        """Should return (False, original) for whitespace-only string."""
        original = '   '
        success, result = parse_json_safe(original)
        assert success is False
        assert result == original

    def test_nested_json_object(self) -> None:
        """Should successfully parse nested JSON object."""
        success, result = parse_json_safe('{"outer": {"inner": "value"}}')
        assert success is True
        assert result == {"outer": {"inner": "value"}}

    def test_complex_json_structure(self) -> None:
        """Should successfully parse complex JSON with mixed types."""
        json_line = '{"id": 1, "active": true, "tags": ["a", "b"], "data": null}'
        success, result = parse_json_safe(json_line)
        assert success is True
        assert result == {"id": 1, "active": True, "tags": ["a", "b"], "data": None}


class TestNeedsTransformation:
    """Tests for needs_transformation function."""

    def test_content_without_structuredcontent_needs_transform(self) -> None:
        """Should return True for response with content but no structuredContent."""
        data = {"result": {"content": []}}
        assert needs_transformation(data) is True

    def test_with_structuredcontent_no_transform_needed(self) -> None:
        """Should return False when structuredContent already exists."""
        data = {"result": {"content": [], "structuredContent": {}}}
        assert needs_transformation(data) is False

    def test_without_result_field(self) -> None:
        """Should return False for data without result field."""
        data = {"id": 1, "error": None}
        assert needs_transformation(data) is False

    def test_with_empty_content_array(self) -> None:
        """Should return True for empty content array (still needs transform)."""
        data = {"result": {"content": []}}
        assert needs_transformation(data) is True

    def test_with_content_items(self) -> None:
        """Should return True for response with content items."""
        data = {"result": {"content": [{"type": "text", "text": "hello"}]}}
        assert needs_transformation(data) is True

    def test_null_result(self) -> None:
        """Should return False when result is None."""
        data = {"result": None}
        assert needs_transformation(data) is False

    def test_non_dict_result(self) -> None:
        """Should return False when result is not a dict."""
        data = {"result": "not a dict"}
        assert needs_transformation(data) is False

    def test_non_dict_data(self) -> None:
        """Should return False when data is not a dict."""
        assert needs_transformation([1, 2, 3]) is False
        assert needs_transformation("string") is False
        assert needs_transformation(42) is False

    def test_result_without_content(self) -> None:
        """Should return False when result has no content field."""
        data = {"result": {"other": "value"}}
        assert needs_transformation(data) is False

    def test_both_content_and_structuredcontent(self) -> None:
        """Should return False when both content and structuredContent exist."""
        data = {
            "result": {
                "content": [{"type": "text"}],
                "structuredContent": {"status": "ok"}
            }
        }
        assert needs_transformation(data) is False
