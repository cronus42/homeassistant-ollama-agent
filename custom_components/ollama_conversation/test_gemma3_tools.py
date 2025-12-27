"""Test gemma3-tools format detection and conversion."""
import json


def _is_gemma3_tool_format(response: dict) -> bool:
    """Detect if response is in gemma3-tools format."""
    if not isinstance(response, dict):
        return False
    
    if "tool_calls" in response:
        return False
    
    has_type_field = "type" in response
    
    if not has_type_field:
        return False
    
    type_val = response.get("type")
    if not isinstance(type_val, str):
        return False
    
    for key in response.keys():
        if key != "type" and ("." in key or key in ["on", "off", "brightness"]):
            return True
    
    return False


def _parse_gemma3_tool_format(response: dict, domain_map: dict = None) -> list:
    """Parse gemma3-tools format and convert to standard tool_calls format."""
    tool_calls = []
    domain = response.get("type", "unknown")
    
    for key, value in response.items():
        if key == "type":
            continue
        
        if key in ["__reasoning__", "text"]:
            continue
        
        entity_id = key if "." in key else f"{domain}.{key}"
        
        if isinstance(value, str):
            action = value.lower()
            
            if domain == "light":
                if action == "on":
                    tool_call = {
                        "function": {
                            "name": "light_turn_on",
                            "arguments": {"entity_id": entity_id}
                        }
                    }
                elif action == "off":
                    tool_call = {
                        "function": {
                            "name": "light_turn_off",
                            "arguments": {"entity_id": entity_id}
                        }
                    }
                else:
                    continue
                    
            elif domain == "climate":
                try:
                    temp = float(value)
                    tool_call = {
                        "function": {
                            "name": "climate_set_temperature",
                            "arguments": {"entity_id": entity_id, "temperature": temp}
                        }
                    }
                except (ValueError, TypeError):
                    continue
            else:
                continue
                
        elif isinstance(value, dict):
            if domain == "light":
                tool_call = {
                    "function": {
                        "name": "light_turn_on",
                        "arguments": {
                            "entity_id": entity_id,
                            **value
                        }
                    }
                }
            elif domain == "climate":
                if "temperature" in value:
                    tool_call = {
                        "function": {
                            "name": "climate_set_temperature",
                            "arguments": {
                                "entity_id": entity_id,
                                "temperature": value["temperature"]
                            }
                        }
                    }
                else:
                    continue
            else:
                continue
        else:
            continue
        
        if "tool_call" in locals():
            tool_calls.append(tool_call)
    
    return tool_calls


def test_gemma3_detection_single_light():
    """Test detection of simple gemma3-tools light format."""
    response = {
        "type": "light",
        "light.desk_lamp": "on"
    }
    assert _is_gemma3_tool_format(response), "Should detect gemma3-tools format"


def test_gemma3_detection_multiple_lights():
    """Test detection with multiple lights."""
    response = {
        "type": "light",
        "light.desk_lamp": "on",
        "light.kitchen": "off"
    }
    assert _is_gemma3_tool_format(response), "Should detect gemma3-tools format with multiple devices"


def test_gemma3_detection_full_entity_id():
    """Test detection with full entity IDs."""
    response = {
        "type": "light",
        "light.desk_lamp": "on",
        "light.living_room": "off"
    }
    assert _is_gemma3_tool_format(response), "Should detect gemma3-tools format with full entity IDs"


def test_standard_format_not_detected_as_gemma3():
    """Test that standard tool_calls format is not detected as gemma3."""
    response = {
        "tool_calls": [
            {
                "function": {
                    "name": "light_turn_on",
                    "arguments": {"entity_id": "light.desk_lamp"}
                }
            }
        ]
    }
    assert not _is_gemma3_tool_format(response), "Should not detect standard format as gemma3"


def test_plain_text_not_detected_as_gemma3():
    """Test that plain text responses are not detected as gemma3."""
    response = {"content": "The light is now on"}
    assert not _is_gemma3_tool_format(response), "Should not detect plain text as gemma3"


def test_parse_gemma3_single_light_on():
    """Test parsing single light on."""
    response = {
        "type": "light",
        "light.desk_lamp": "on"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 1, "Should have one tool call"
    assert tool_calls[0]["function"]["name"] == "light_turn_on"
    assert tool_calls[0]["function"]["arguments"]["entity_id"] == "light.desk_lamp"


def test_parse_gemma3_single_light_off():
    """Test parsing single light off."""
    response = {
        "type": "light",
        "light.desk_lamp": "off"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "light_turn_off"
    assert tool_calls[0]["function"]["arguments"]["entity_id"] == "light.desk_lamp"


def test_parse_gemma3_multiple_lights():
    """Test parsing multiple lights."""
    response = {
        "type": "light",
        "light.desk_lamp": "on",
        "light.kitchen": "off",
        "light.bedroom": "on"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 3
    names = [tc["function"]["name"] for tc in tool_calls]
    assert names.count("light_turn_on") == 2
    assert names.count("light_turn_off") == 1


def test_parse_gemma3_light_with_brightness():
    """Test parsing light with brightness."""
    response = {
        "type": "light",
        "light.desk_lamp": {"brightness": 200}
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "light_turn_on"
    assert tool_calls[0]["function"]["arguments"]["entity_id"] == "light.desk_lamp"
    assert tool_calls[0]["function"]["arguments"]["brightness"] == 200


def test_parse_gemma3_climate_temperature():
    """Test parsing climate temperature set."""
    response = {
        "type": "climate",
        "climate.bedroom": "72"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "climate_set_temperature"
    assert tool_calls[0]["function"]["arguments"]["entity_id"] == "climate.bedroom"
    assert tool_calls[0]["function"]["arguments"]["temperature"] == 72.0


def test_parse_gemma3_climate_with_dict():
    """Test parsing climate with dict format."""
    response = {
        "type": "climate",
        "climate.bedroom": {"temperature": 68}
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "climate_set_temperature"
    assert tool_calls[0]["function"]["arguments"]["temperature"] == 68


def test_parse_gemma3_mixed_actions():
    """Test parsing mixed light actions."""
    response = {
        "type": "light",
        "light.desk_lamp": "on",
        "light.kitchen": {"brightness": 150},
        "light.bedroom": "off"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 3
    
    # Find each tool call
    turn_on_calls = [tc for tc in tool_calls if tc["function"]["name"] == "light_turn_on"]
    turn_off_calls = [tc for tc in tool_calls if tc["function"]["name"] == "light_turn_off"]
    
    assert len(turn_on_calls) == 2
    assert len(turn_off_calls) == 1
    
    # Check brightness
    brightness_call = [tc for tc in turn_on_calls if "brightness" in tc["function"]["arguments"]]
    assert len(brightness_call) == 1
    assert brightness_call[0]["function"]["arguments"]["brightness"] == 150


def test_parse_gemma3_with_content_field():
    """Test that content field is not treated as action."""
    response = {
        "type": "light",
        "light.desk_lamp": "on",
        "content": "The light is now on"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["arguments"]["entity_id"] == "light.desk_lamp"


def test_parse_gemma3_invalid_domain():
    """Test handling of invalid domain."""
    response = {
        "type": "invalid_domain",
        "invalid.device": "on"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 0


def test_parse_gemma3_invalid_action():
    """Test handling of invalid action."""
    response = {
        "type": "light",
        "light.desk_lamp": "invalid_action"
    }
    tool_calls = _parse_gemma3_tool_format(response)
    
    assert len(tool_calls) == 0


if __name__ == "__main__":
    test_gemma3_detection_single_light()
    print("✓ test_gemma3_detection_single_light")
    
    test_gemma3_detection_multiple_lights()
    print("✓ test_gemma3_detection_multiple_lights")
    
    test_gemma3_detection_full_entity_id()
    print("✓ test_gemma3_detection_full_entity_id")
    
    test_standard_format_not_detected_as_gemma3()
    print("✓ test_standard_format_not_detected_as_gemma3")
    
    test_plain_text_not_detected_as_gemma3()
    print("✓ test_plain_text_not_detected_as_gemma3")
    
    test_parse_gemma3_single_light_on()
    print("✓ test_parse_gemma3_single_light_on")
    
    test_parse_gemma3_single_light_off()
    print("✓ test_parse_gemma3_single_light_off")
    
    test_parse_gemma3_multiple_lights()
    print("✓ test_parse_gemma3_multiple_lights")
    
    test_parse_gemma3_light_with_brightness()
    print("✓ test_parse_gemma3_light_with_brightness")
    
    test_parse_gemma3_climate_temperature()
    print("✓ test_parse_gemma3_climate_temperature")
    
    test_parse_gemma3_climate_with_dict()
    print("✓ test_parse_gemma3_climate_with_dict")
    
    test_parse_gemma3_mixed_actions()
    print("✓ test_parse_gemma3_mixed_actions")
    
    test_parse_gemma3_with_content_field()
    print("✓ test_parse_gemma3_with_content_field")
    
    test_parse_gemma3_invalid_domain()
    print("✓ test_parse_gemma3_invalid_domain")
    
    test_parse_gemma3_invalid_action()
    print("✓ test_parse_gemma3_invalid_action")
    
    print("\n✅ All 15 tests passed!")
