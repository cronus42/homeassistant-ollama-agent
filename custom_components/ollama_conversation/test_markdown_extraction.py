"""Tests for markdown JSON extraction in gemma3-tools format."""
import pytest
from custom_components.ollama_conversation.conversation import (
    _extract_json_from_markdown,
    _is_gemma3_tool_format,
    _parse_gemma3_tool_format,
)


class TestMarkdownJsonExtraction:
    """Test the _extract_json_from_markdown function."""

    def test_extract_json_with_json_fence(self):
        """Test extracting JSON from markdown with 'json' language identifier."""
        content = """Here's the tool call:
```json
{"type": "light", "entity_id": "light.desk_lamp"}
```
"""
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["type"] == "light"
        assert result["entity_id"] == "light.desk_lamp"

    def test_extract_json_without_language_identifier(self):
        """Test extracting JSON from markdown without language identifier."""
        content = """```
{"type": "climate", "entity_id": "climate.bedroom", "temperature": 72}
```"""
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["type"] == "climate"
        assert result["entity_id"] == "climate.bedroom"
        assert result["temperature"] == 72

    def test_extract_json_with_whitespace(self):
        """Test extracting JSON with extra whitespace."""
        content = """```json

{"type": "light", "light.kitchen": "on"}

```"""
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["type"] == "light"
        assert result["light.kitchen"] == "on"

    def test_extract_json_direct_json(self):
        """Test parsing direct JSON without markdown fences."""
        content = '{"type": "light", "entity_id": "light.bedroom"}'
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["type"] == "light"
        assert result["entity_id"] == "light.bedroom"

    def test_extract_json_invalid_json(self):
        """Test handling of invalid JSON."""
        content = """```json
{this is not valid json}
```"""
        result = _extract_json_from_markdown(content)
        assert result is None

    def test_extract_json_no_json_content(self):
        """Test handling of text without JSON."""
        content = "Just some regular text without any JSON"
        result = _extract_json_from_markdown(content)
        assert result is None

    def test_extract_json_non_string_input(self):
        """Test handling of non-string input."""
        result = _extract_json_from_markdown(None)
        assert result is None
        
        result = _extract_json_from_markdown(123)
        assert result is None
        
        result = _extract_json_from_markdown({"already": "a dict"})
        assert result is None

    def test_extract_json_multiple_code_blocks(self):
        """Test extracting from first valid JSON block when multiple exist."""
        content = """```
invalid json here
```

```json
{"type": "light", "entity_id": "light.hallway"}
```"""
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["type"] == "light"
        assert result["entity_id"] == "light.hallway"

    def test_extract_json_with_complex_structure(self):
        """Test extracting complex JSON with nested objects."""
        content = """```json
{
  "type": "light",
  "light.living_room": {"brightness": 200, "color": "warm_white"}
}
```"""
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["type"] == "light"
        assert result["light.living_room"]["brightness"] == 200
        assert result["light.living_room"]["color"] == "warm_white"


class TestMarkdownGemma3Integration:
    """Test integration of markdown extraction with gemma3-tools format detection."""

    def test_markdown_gemma3_format_detection(self):
        """Test that markdown-wrapped gemma3 format is detected."""
        content = """```json
{"type": "light", "light.desk_lamp": "on"}
```"""
        
        json_data = _extract_json_from_markdown(content)
        assert json_data is not None
        assert _is_gemma3_tool_format(json_data) is True

    def test_markdown_gemma3_format_parsing(self):
        """Test parsing gemma3 format from markdown."""
        content = """```json
{"type": "light", "light.kitchen": "on"}
```"""
        
        json_data = _extract_json_from_markdown(content)
        tool_calls = _parse_gemma3_tool_format(json_data)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "light_turn_on"
        assert tool_calls[0]["function"]["arguments"]["entity_id"] == "light.kitchen"

    def test_markdown_gemma3_with_brightness(self):
        """Test parsing gemma3 format with brightness from markdown."""
        content = """```json
{"type": "light", "light.bedroom": {"brightness": 150}}
```"""
        
        json_data = _extract_json_from_markdown(content)
        tool_calls = _parse_gemma3_tool_format(json_data)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "light_turn_on"
        assert tool_calls[0]["function"]["arguments"]["entity_id"] == "light.bedroom"
        assert tool_calls[0]["function"]["arguments"]["brightness"] == 150

    def test_markdown_gemma3_climate_control(self):
        """Test parsing gemma3 climate control from markdown."""
        content = """```json
{"type": "climate", "climate.bedroom": {"temperature": 72}}
```"""
        
        json_data = _extract_json_from_markdown(content)
        tool_calls = _parse_gemma3_tool_format(json_data)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "climate_set_temperature"
        assert tool_calls[0]["function"]["arguments"]["entity_id"] == "climate.bedroom"
        assert tool_calls[0]["function"]["arguments"]["temperature"] == 72

    def test_markdown_gemma3_multiple_lights(self):
        """Test parsing multiple light commands from markdown."""
        content = """```json
{
  "type": "light",
  "light.kitchen": "on",
  "light.living_room": {"brightness": 200}
}
```"""
        
        json_data = _extract_json_from_markdown(content)
        tool_calls = _parse_gemma3_tool_format(json_data)
        
        assert len(tool_calls) == 2
        
        # Check both tool calls were created
        entity_ids = [tc["function"]["arguments"]["entity_id"] for tc in tool_calls]
        assert "light.kitchen" in entity_ids
        assert "light.living_room" in entity_ids

    def test_markdown_non_gemma3_format(self):
        """Test that non-gemma3 JSON in markdown is not detected as gemma3."""
        content = """```json
{"some_other": "format", "not": "gemma3"}
```"""
        
        json_data = _extract_json_from_markdown(content)
        assert json_data is not None
        assert _is_gemma3_tool_format(json_data) is False

    def test_markdown_with_explanation_text(self):
        """Test extracting JSON when model includes explanation text."""
        content = """I'll help you turn on that light.

```json
{"type": "light", "light.desk_lamp": "on"}
```

The light should be on now!"""
        
        json_data = _extract_json_from_markdown(content)
        assert json_data is not None
        assert _is_gemma3_tool_format(json_data) is True
        
        tool_calls = _parse_gemma3_tool_format(json_data)
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["arguments"]["entity_id"] == "light.desk_lamp"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string(self):
        """Test handling of empty string."""
        result = _extract_json_from_markdown("")
        assert result is None

    def test_whitespace_only(self):
        """Test handling of whitespace-only string."""
        result = _extract_json_from_markdown("   \n\n  ")
        assert result is None

    def test_markdown_fence_no_content(self):
        """Test markdown fence with no JSON content."""
        content = "```json\n```"
        result = _extract_json_from_markdown(content)
        assert result is None

    def test_malformed_markdown_fence(self):
        """Test malformed markdown fences."""
        content = "``json"  # Only two backticks
        result = _extract_json_from_markdown(content)
        assert result is None

    def test_json_with_escaped_characters(self):
        """Test JSON with escaped characters."""
        content = """```json
{"type": "light", "entity_id": "light.guest_room"}
```"""
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["entity_id"] == "light.guest_room"

    def test_json_with_unicode(self):
        """Test JSON with unicode characters."""
        content = """```json
{"type": "climate", "entity_id": "climate.café"}
```"""
        result = _extract_json_from_markdown(content)
        assert result is not None
        assert result["entity_id"] == "climate.café"
