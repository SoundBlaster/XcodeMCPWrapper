"""
Unit tests for the transform module.
"""

import json

import pytest

from mcpbridge_wrapper.transform import (
    extract_text_content,
    inject_structured_content,
    is_json_line,
    needs_transformation,
    parse_json_safe,
    parse_structured_content,
    parse_structured_content_with_fallback,
    process_response_line,
)


class TestIsJsonLine:
    """Tests for is_json_line function."""

    def test_valid_json_object(self) -> None:
        """Should return True for valid JSON object."""
        assert is_json_line('{"key": "value"}') is True

    def test_valid_json_array(self) -> None:
        """Should return True for valid JSON array."""
        assert is_json_line("[1, 2, 3]") is True

    def test_valid_json_string_primitive(self) -> None:
        """Should return True for JSON string primitive."""
        assert is_json_line('"plain string"') is True

    def test_valid_json_number_primitive(self) -> None:
        """Should return True for JSON number primitive."""
        assert is_json_line("42") is True

    def test_valid_json_boolean_true(self) -> None:
        """Should return True for JSON boolean true."""
        assert is_json_line("true") is True

    def test_valid_json_boolean_false(self) -> None:
        """Should return True for JSON boolean false."""
        assert is_json_line("false") is True

    def test_valid_json_null(self) -> None:
        """Should return True for JSON null."""
        assert is_json_line("null") is True

    def test_plain_text_rejection(self) -> None:
        """Should return False for plain text log."""
        assert is_json_line("Plain text log") is False

    def test_plain_text_with_colon(self) -> None:
        """Should return False for plain text with colon."""
        assert is_json_line("Error: something went wrong") is False

    def test_partial_json_rejection(self) -> None:
        """Should return False for partial/broken JSON."""
        assert is_json_line('{"broken') is False

    def test_empty_string(self) -> None:
        """Should return False for empty string."""
        assert is_json_line("") is False

    def test_whitespace_only(self) -> None:
        """Should return False for whitespace-only string."""
        assert is_json_line("   ") is False

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
        success, result = parse_json_safe("[1, 2, 3]")
        assert success is True
        assert result == [1, 2, 3]

    def test_valid_json_string_primitive(self) -> None:
        """Should return (True, string) for JSON string primitive."""
        success, result = parse_json_safe('"plain string"')
        assert success is True
        assert result == "plain string"

    def test_valid_json_number_primitive(self) -> None:
        """Should return (True, number) for JSON number primitive."""
        success, result = parse_json_safe("42")
        assert success is True
        assert result == 42

    def test_valid_json_boolean(self) -> None:
        """Should return (True, bool) for JSON boolean."""
        success, result = parse_json_safe("true")
        assert success is True
        assert result is True

    def test_valid_json_null(self) -> None:
        """Should return (True, None) for JSON null."""
        success, result = parse_json_safe("null")
        assert success is True
        assert result is None

    def test_invalid_json_returns_failure_with_original(self) -> None:
        """Should return (False, original_line) for invalid JSON."""
        original = "invalid json"
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
        original = ""
        success, result = parse_json_safe(original)
        assert success is False
        assert result == original

    def test_whitespace_only_returns_failure(self) -> None:
        """Should return (False, original) for whitespace-only string."""
        original = "   "
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
        """Should return True for response with content items but no structuredContent."""
        data = {"result": {"content": [{"type": "text", "text": "data"}]}}
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
        """Should return False for empty content array (nothing to transform)."""
        data = {"result": {"content": []}}
        assert needs_transformation(data) is False

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
        data = {"result": {"content": [{"type": "text"}], "structuredContent": {"status": "ok"}}}
        assert needs_transformation(data) is False


class TestExtractTextContent:
    """Tests for extract_text_content function."""

    def test_mixed_content_extracts_first_text(self) -> None:
        """Should extract text from first text item in mixed content."""
        content = [{"type": "image"}, {"type": "text", "text": "data"}]
        assert extract_text_content(content) == "data"

    def test_single_text_item(self) -> None:
        """Should extract text from single text item."""
        content = [{"type": "text", "text": "hello world"}]
        assert extract_text_content(content) == "hello world"

    def test_multiple_text_items_returns_first(self) -> None:
        """Should return text from first text item when multiple exist."""
        content = [{"type": "text", "text": "first"}, {"type": "text", "text": "second"}]
        assert extract_text_content(content) == "first"

    def test_no_text_items_returns_none(self) -> None:
        """Should return None when no text items exist."""
        content = [{"type": "image"}, {"type": "image"}]
        assert extract_text_content(content) is None

    def test_empty_content_array(self) -> None:
        """Should return None for empty content array."""
        assert extract_text_content([]) is None

    def test_text_item_without_text_field(self) -> None:
        """Should skip text items without text field."""
        content = [{"type": "text"}, {"type": "text", "text": "has text"}]
        assert extract_text_content(content) == "has text"

    def test_non_dict_items_skipped(self) -> None:
        """Should skip non-dict items in content array."""
        content = ["not a dict", {"type": "text", "text": "found"}]
        assert extract_text_content(content) == "found"

    def test_text_field_not_string(self) -> None:
        """Should skip items where text field is not a string."""
        content = [{"type": "text", "text": 123}, {"type": "text", "text": "string"}]
        assert extract_text_content(content) == "string"

    def test_text_field_none(self) -> None:
        """Should skip items where text field is None."""
        content = [{"type": "text", "text": None}, {"type": "text", "text": "value"}]
        assert extract_text_content(content) == "value"

    def test_complex_mcp_response_content(self) -> None:
        """Should handle realistic MCP response content structure."""
        content = [
            {"type": "image", "url": "http://example.com/img.png"},
            {"type": "text", "text": '{"result": "success"}'},
        ]
        assert extract_text_content(content) == '{"result": "success"}'


class TestParseStructuredContent:
    """Tests for parse_structured_content function."""

    def test_valid_json_object_string(self) -> None:
        """Should parse JSON object string into dict."""
        result = parse_structured_content('{"result": true}')
        assert result == {"result": True}

    def test_valid_json_array_string(self) -> None:
        """Should parse JSON array string into list."""
        result = parse_structured_content("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_json_string_primitive(self) -> None:
        """Should parse JSON string primitive."""
        result = parse_structured_content('"plain string"')
        assert result == "plain string"

    def test_json_number_primitive(self) -> None:
        """Should parse JSON number primitive."""
        result = parse_structured_content("42")
        assert result == 42

    def test_json_boolean_true(self) -> None:
        """Should parse JSON boolean true."""
        result = parse_structured_content("true")
        assert result is True

    def test_json_boolean_false(self) -> None:
        """Should parse JSON boolean false."""
        result = parse_structured_content("false")
        assert result is False

    def test_json_null(self) -> None:
        """Should parse JSON null."""
        result = parse_structured_content("null")
        assert result is None

    def test_invalid_json_raises_exception(self) -> None:
        """Should raise JSONDecodeError for invalid JSON."""
        import json

        with pytest.raises(json.JSONDecodeError):
            parse_structured_content("invalid json")

    def test_partial_json_raises_exception(self) -> None:
        """Should raise JSONDecodeError for partial JSON."""
        import json

        with pytest.raises(json.JSONDecodeError):
            parse_structured_content('{"broken')

    def test_empty_string_raises_exception(self) -> None:
        """Should raise JSONDecodeError for empty string."""
        import json

        with pytest.raises(json.JSONDecodeError):
            parse_structured_content("")

    def test_nested_json_object(self) -> None:
        """Should parse nested JSON object."""
        result = parse_structured_content('{"outer": {"inner": "value"}}')
        assert result == {"outer": {"inner": "value"}}

    def test_complex_mcp_response_payload(self) -> None:
        """Should parse realistic MCP response payload."""
        text = '{"buildResult": "success", "elapsedTime": 2.17, "errors": []}'
        result = parse_structured_content(text)
        assert result == {"buildResult": "success", "elapsedTime": 2.17, "errors": []}


class TestParseStructuredContentWithFallback:
    """Tests for parse_structured_content_with_fallback function."""

    def test_valid_json_object_returns_parsed(self) -> None:
        """Should return parsed JSON object for valid JSON."""
        result = parse_structured_content_with_fallback('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_json_array_returns_parsed(self) -> None:
        """Should return parsed JSON array for valid JSON."""
        result = parse_structured_content_with_fallback("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_json_string_primitive_returns_string(self) -> None:
        """Should return string primitive for JSON string."""
        result = parse_structured_content_with_fallback('"plain string"')
        assert result == "plain string"

    def test_non_json_text_gets_wrapped(self) -> None:
        """Should wrap non-JSON text in {text: ...} structure."""
        result = parse_structured_content_with_fallback("error message")
        assert result == {"text": "error message"}

    def test_empty_string_gets_wrapped(self) -> None:
        """Should wrap empty string in {text: ...} structure."""
        result = parse_structured_content_with_fallback("")
        assert result == {"text": ""}

    def test_partial_json_gets_wrapped(self) -> None:
        """Should wrap partial/broken JSON in {text: ...} structure."""
        result = parse_structured_content_with_fallback('{"broken')
        assert result == {"text": '{"broken'}

    def test_plain_text_with_special_chars_gets_wrapped(self) -> None:
        """Should wrap plain text with special chars in {text: ...}."""
        text = "Error: Something went wrong! (code: 500)"
        result = parse_structured_content_with_fallback(text)
        assert result == {"text": text}

    def test_multiline_text_gets_wrapped(self) -> None:
        """Should wrap multiline non-JSON text in {text: ...}."""
        text = "Line 1\nLine 2\nLine 3"
        result = parse_structured_content_with_fallback(text)
        assert result == {"text": text}

    def test_json_null_returns_none(self) -> None:
        """Should return None for JSON null."""
        result = parse_structured_content_with_fallback("null")
        assert result is None

    def test_json_boolean_returns_bool(self) -> None:
        """Should return bool for JSON boolean."""
        result = parse_structured_content_with_fallback("true")
        assert result is True


class TestInjectStructuredContent:
    """Tests for inject_structured_content function."""

    def test_injects_structuredcontent_for_valid_json(self) -> None:
        """Should inject structuredContent with parsed JSON."""
        data = {"result": {"content": [{"type": "text", "text": '{"status": "ok"}'}]}}
        inject_structured_content(data)
        assert data["result"]["structuredContent"] == {"status": "ok"}

    def test_injects_structuredcontent_for_non_json(self) -> None:
        """Should inject structuredContent with fallback wrapper for non-JSON."""
        data = {"result": {"content": [{"type": "text", "text": "plain error"}]}}
        inject_structured_content(data)
        assert data["result"]["structuredContent"] == {"text": "plain error"}

    def test_preserves_content_array(self) -> None:
        """Should preserve original content array after injection."""
        data = {"result": {"content": [{"type": "text", "text": "{}"}]}}
        inject_structured_content(data)
        assert data["result"]["content"] == [{"type": "text", "text": "{}"}]

    def test_mutation_in_place(self) -> None:
        """Should mutate the data dictionary in place."""
        data = {"result": {"content": [{"type": "text", "text": "[]"}]}}
        result = inject_structured_content(data)
        assert result is None
        assert "structuredContent" in data["result"]

    def test_no_result_key(self) -> None:
        """Should handle data without result key gracefully."""
        data = {"id": 1, "error": None}
        inject_structured_content(data)
        assert "structuredContent" not in data.get("result", {})

    def test_result_not_dict(self) -> None:
        """Should handle non-dict result gracefully."""
        data = {"result": "not a dict"}
        inject_structured_content(data)
        assert "structuredContent" not in data["result"]

    def test_no_content_key(self) -> None:
        """Should handle result without content key gracefully."""
        data = {"result": {"other": "value"}}
        inject_structured_content(data)
        assert "structuredContent" not in data["result"]

    def test_content_not_list(self) -> None:
        """Should handle non-list content gracefully."""
        data = {"result": {"content": "not a list"}}
        inject_structured_content(data)
        assert "structuredContent" not in data["result"]

    def test_no_text_items(self) -> None:
        """Should handle content with no text items gracefully."""
        data = {"result": {"content": [{"type": "image"}]}}
        inject_structured_content(data)
        assert "structuredContent" not in data["result"]

    def test_empty_content_array(self) -> None:
        """Should handle empty content array gracefully."""
        data = {"result": {"content": []}}
        inject_structured_content(data)
        assert "structuredContent" not in data["result"]

    def test_complex_json_payload(self) -> None:
        """Should handle complex JSON payload correctly."""
        data = {
            "result": {
                "content": [
                    {"type": "text", "text": '{"buildResult": "success", "elapsedTime": 2.17}'}
                ]
            }
        }
        inject_structured_content(data)
        assert data["result"]["structuredContent"] == {
            "buildResult": "success",
            "elapsedTime": 2.17,
        }

    def test_json_array_payload(self) -> None:
        """Should handle JSON array payload correctly."""
        data = {"result": {"content": [{"type": "text", "text": "[1, 2, 3]"}]}}
        inject_structured_content(data)
        assert data["result"]["structuredContent"] == [1, 2, 3]


class TestProcessResponseLine:
    """Tests for process_response_line function."""

    def test_json_line_with_trailing_newline_gets_transformed(self) -> None:
        """Should transform a JSON line even if it includes a trailing newline."""
        line = (
            '{"result": {"content": [{"type": "text", "text": "{\\"status\\": \\"ok\\"}"}]}}'
            "\n"
        )
        result = process_response_line(line)

        # Behavior: transformation occurs; output formatting (like preserving the newline)
        # is not guaranteed by the transformer.
        parsed = json.loads(result)
        assert parsed["result"]["structuredContent"] == {"status": "ok"}

    def test_plain_text_passthrough(self) -> None:
        """Should pass through plain text unchanged."""
        line = "This is a log message"
        result = process_response_line(line)
        assert result == line

    def test_non_json_error_message(self) -> None:
        """Should pass through non-JSON error messages."""
        line = "Error: Something went wrong!"
        result = process_response_line(line)
        assert result == line

    def test_json_needing_transformation(self) -> None:
        """Should transform JSON that needs structuredContent."""
        line = '{"result": {"content": [{"type": "text", "text": "{\\"status\\": \\"ok\\"}"}]}}'
        result = process_response_line(line)
        parsed = json.loads(result)
        assert "structuredContent" in parsed["result"]
        assert parsed["result"]["structuredContent"] == {"status": "ok"}

    def test_already_compliant_json(self) -> None:
        """Should pass through JSON that already has structuredContent."""
        line = '{"result": {"content": [], "structuredContent": {}}}'
        result = process_response_line(line)
        assert result == line

    def test_non_result_json(self) -> None:
        """Should pass through JSON without result field."""
        line = '{"id": 1, "error": null}'
        result = process_response_line(line)
        assert result == line

    def test_empty_line(self) -> None:
        """Should pass through empty line."""
        line = ""
        result = process_response_line(line)
        assert result == ""

    def test_whitespace_only(self) -> None:
        """Should pass through whitespace-only line."""
        line = "   "
        result = process_response_line(line)
        assert result == "   "

    def test_partial_json(self) -> None:
        """Should pass through partial/broken JSON unchanged."""
        line = '{"broken'
        result = process_response_line(line)
        assert result == line

    def test_json_with_non_json_text_content(self) -> None:
        """Should wrap non-JSON text content in fallback."""
        line = '{"result": {"content": [{"type": "text", "text": "plain error"}]}}'
        result = process_response_line(line)
        parsed = json.loads(result)
        assert parsed["result"]["structuredContent"] == {"text": "plain error"}

    def test_preserves_other_json_fields(self) -> None:
        """Should preserve other fields in the JSON when transforming."""
        line = (
            '{"id": 123, "result": {"content": [{"type": "text", "text": "[]"}]}, "jsonrpc": "2.0"}'
        )
        result = process_response_line(line)
        parsed = json.loads(result)
        assert parsed["id"] == 123
        assert parsed["jsonrpc"] == "2.0"
        assert "structuredContent" in parsed["result"]

    def test_image_only_content_no_transformation(self) -> None:
        """Should not transform responses with only image content (EC3)."""
        line = '{"result": {"content": [{"type": "image", "url": "http://example.com/img.png"}]}}'
        result = process_response_line(line)
        assert result == line
        parsed = json.loads(result)
        assert "structuredContent" not in parsed["result"]

    def test_multiple_images_no_transformation(self) -> None:
        """Should not transform responses with multiple image items."""
        line = '{"result": {"content": [{"type": "image", "url": "img1.png"}, '
        line += '{"type": "image", "url": "img2.png"}]}}'
        result = process_response_line(line)
        assert result == line
        parsed = json.loads(result)
        assert "structuredContent" not in parsed["result"]

    def test_non_text_types_no_transformation(self) -> None:
        """Should not transform responses with non-text content types."""
        line = '{"result": {"content": [{"type": "file", "path": "/tmp/data.bin"}]}}'
        result = process_response_line(line)
        assert result == line
        parsed = json.loads(result)
        assert "structuredContent" not in parsed["result"]
