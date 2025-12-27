"""Test the think block filtering functionality."""
import re


def _filter_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks from response text.
    
    This filters out internal reasoning blocks that should not be shown to users.
    Handles multiple blocks and various formatting variations.
    """
    if not text:
        return text
    
    pattern = r'<think>.*?</think>'
    cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


def test_single_think_block():
    """Test filtering a single think block."""
    text = "<think>This is internal reasoning</think>\nThe lamp has been turned off."
    result = _filter_think_blocks(text)
    assert result == "The lamp has been turned off.", f"Expected 'The lamp has been turned off.' but got '{result}'"
    assert "<think>" not in result


def test_multiple_think_blocks():
    """Test filtering multiple think blocks in one response."""
    text = "<think>First reasoning</think>\nSome content\n<think>Second reasoning</think>\nMore content"
    result = _filter_think_blocks(text)
    assert result == "Some content\nMore content", f"Expected 'Some content\nMore content' but got '{result}'"
    assert "<think>" not in result


def test_multiline_think_block():
    """Test filtering multiline think blocks."""
    text = """<think>
    This is a multiline
    reasoning block
    with multiple lines
</think>

The actual response here."""
    result = _filter_think_blocks(text)
    assert "multiline" not in result
    assert "The actual response here." in result
    assert "<think>" not in result


def test_case_insensitive():
    """Test that filtering is case-insensitive."""
    text = "<THINK>Some reasoning</THINK>\nActual response"
    result = _filter_think_blocks(text)
    assert result == "Actual response", f"Expected 'Actual response' but got '{result}'"
    assert "<THINK>" not in result


def test_no_think_blocks():
    """Test with text that has no think blocks."""
    text = "This is a normal response without any think blocks."
    result = _filter_think_blocks(text)
    assert result == text


def test_empty_think_block():
    """Test with empty think blocks."""
    text = "<think></think>\nResponse text"
    result = _filter_think_blocks(text)
    assert result == "Response text", f"Expected 'Response text' but got '{result}'"


def test_nested_tags_in_think():
    """Test with complex content inside think blocks."""
    text = "<think>The user wants to turn on light.kitchen with brightness 255</think>\nTurning on the light."
    result = _filter_think_blocks(text)
    assert result == "Turning on the light.", f"Expected 'Turning on the light.' but got '{result}'"
    assert "light.kitchen" not in result


def test_whitespace_cleanup():
    """Test that excessive whitespace is cleaned up."""
    text = "<think>reasoning</think>\n\n\nResponse after multiple newlines"
    result = _filter_think_blocks(text)
    assert "\n\n\n" not in result
    assert "Response after multiple newlines" in result


def test_real_world_example():
    """Test with a realistic example from the agent."""
    text = """<think>
The user asked to turn off the living room lamp. I need to:
1. Identify the correct entity_id for the living room lamp
2. Call the light_turn_off tool with that entity_id
3. Report the result to the user
</think>

I'll turn off the lamp in the living room for you.
Successfully turned off light.living_room"""
    
    result = _filter_think_blocks(text)
    assert "<think>" not in result
    assert "living room lamp" not in result
    assert "Successfully turned off light.living_room" in result


if __name__ == "__main__":
    # Run tests
    test_single_think_block()
    print("✓ test_single_think_block passed")
    
    test_multiple_think_blocks()
    print("✓ test_multiple_think_blocks passed")
    
    test_multiline_think_block()
    print("✓ test_multiline_think_block passed")
    
    test_case_insensitive()
    print("✓ test_case_insensitive passed")
    
    test_no_think_blocks()
    print("✓ test_no_think_blocks passed")
    
    test_empty_think_block()
    print("✓ test_empty_think_block passed")
    
    test_nested_tags_in_think()
    print("✓ test_nested_tags_in_think passed")
    
    test_whitespace_cleanup()
    print("✓ test_whitespace_cleanup passed")
    
    test_real_world_example()
    print("✓ test_real_world_example passed")
    
    print("\n✅ All tests passed!")
