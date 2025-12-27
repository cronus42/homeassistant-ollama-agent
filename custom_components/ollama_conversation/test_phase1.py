"""Tests for Phase 1: Entity Context Implementation"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.components.conversation import ConversationInput, ConversationResult
from custom_components.ollama_conversation.conversation import OllamaConversationEntity
from custom_components.ollama_conversation.helpers import (
    async_get_exposed_entities,
    format_entities_for_prompt,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.states = MagicMock()
    hass.services = MagicMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.data = {
        "model": "qwen3",
        "url": "http://localhost:11434",
        "temperature": 0.7,
    }
    return entry


class TestHelpers:
    """Test helper functions for entity management."""

    @pytest.mark.asyncio
    async def test_format_entities_for_prompt_empty(self):
        """Test formatting with no entities."""
        result = format_entities_for_prompt({})
        assert "No devices are currently exposed" in result

    @pytest.mark.asyncio
    async def test_format_entities_for_prompt_lights(self):
        """Test formatting with light entities."""
        entities = {
            "light.living_room": {
                "friendly_name": "Living Room Light",
                "state": "on",
                "domain": "light",
                "area_name": "Living Room",
            },
            "light.bedroom": {
                "friendly_name": "Bedroom Light", 
                "state": "off",
                "domain": "light",
                "area_name": "Bedroom",
            },
        }
        
        result = format_entities_for_prompt(entities)
        assert "Available Smart Home Devices" in result
        assert "Lights" in result
        assert "light.living_room" in result
        assert "Living Room Light" in result
        assert "Living Room" in result
        assert "on" in result
        assert "light.bedroom" in result
        assert "off" in result

    @pytest.mark.asyncio
    async def test_format_entities_for_prompt_mixed(self):
        """Test formatting with multiple entity types."""
        entities = {
            "light.kitchen": {
                "friendly_name": "Kitchen Light",
                "state": "on",
                "domain": "light",
            },
            "climate.bedroom": {
                "friendly_name": "Bedroom Climate",
                "state": "72F",
                "domain": "climate",
                "area_name": "Bedroom",
            },
        }
        
        result = format_entities_for_prompt(entities)
        assert "Lights" in result
        assert "Climate Control" in result
        assert "light.kitchen" in result
        assert "climate.bedroom" in result


class TestSystemPrompt:
    """Test system prompt generation."""

    @pytest.mark.asyncio
    async def test_build_system_prompt_includes_entities(self, mock_hass, mock_config_entry):
        """Test that system prompt includes entity context."""
        # Mock entity gathering
        with patch(
            "custom_components.ollama_conversation.conversation.async_get_exposed_entities"
        ) as mock_get_entities:
            mock_get_entities.return_value = {
                "light.living_room": {
                    "friendly_name": "Living Room",
                    "state": "off",
                    "domain": "light",
                },
            }
            
            entity = OllamaConversationEntity(mock_hass, mock_config_entry)
            prompt = await entity._build_system_prompt()
            
            # Verify prompt includes key elements
            assert "Home Assistant assistant" in prompt
            assert "light.living_room" in prompt
            assert "Living Room" in prompt
            assert "light_turn_on" in prompt
            assert "light_turn_off" in prompt
            assert "climate_set_temperature" in prompt
            assert "entity_id" in prompt

    @pytest.mark.asyncio
    async def test_build_system_prompt_instructions(self, mock_hass, mock_config_entry):
        """Test that system prompt includes proper instructions."""
        with patch(
            "custom_components.ollama_conversation.conversation.async_get_exposed_entities"
        ) as mock_get_entities:
            mock_get_entities.return_value = {}
            
            entity = OllamaConversationEntity(mock_hass, mock_config_entry)
            prompt = await entity._build_system_prompt()
            
            # Verify key instructions
            assert "EXACT entity_id" in prompt
            assert "domain.device_name" in prompt
            assert "find the matching entity_id" in prompt
            assert "ask the user for clarification" in prompt


class TestToolExecution:
    """Test tool execution with validation."""

    @pytest.mark.asyncio
    async def test_execute_light_turn_on_success(self, mock_hass, mock_config_entry):
        """Test successful light turn on."""
        mock_hass.services.async_call = AsyncMock()
        entity = OllamaConversationEntity(mock_hass, mock_config_entry)
        
        tool_call = {
            "function": {
                "name": "light_turn_on",
                "arguments": '{"entity_id": "light.kitchen"}',
            }
        }
        
        result = await entity._execute_tool_call(tool_call)
        
        assert "Successfully turned on" in result
        assert "light.kitchen" in result
        mock_hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_light_turn_on_with_brightness(self, mock_hass, mock_config_entry):
        """Test light turn on with brightness."""
        mock_hass.services.async_call = AsyncMock()
        entity = OllamaConversationEntity(mock_hass, mock_config_entry)
        
        tool_call = {
            "function": {
                "name": "light_turn_on",
                "arguments": '{"entity_id": "light.kitchen", "brightness": 128}',
            }
        }
        
        result = await entity._execute_tool_call(tool_call)
        
        assert "Successfully turned on" in result
        assert "128 brightness" in result

    @pytest.mark.asyncio
    async def test_execute_light_turn_on_missing_entity_id(self, mock_hass, mock_config_entry):
        """Test light turn on with missing entity_id."""
        entity = OllamaConversationEntity(mock_hass, mock_config_entry)
        
        tool_call = {
            "function": {
                "name": "light_turn_on",
                "arguments": '{"brightness": 128}',
            }
        }
        
        result = await entity._execute_tool_call(tool_call)
        
        assert "Error" in result
        assert "requires entity_id" in result

    @pytest.mark.asyncio
    async def test_execute_light_turn_off_success(self, mock_hass, mock_config_entry):
        """Test successful light turn off."""
        mock_hass.services.async_call = AsyncMock()
        entity = OllamaConversationEntity(mock_hass, mock_config_entry)
        
        tool_call = {
            "function": {
                "name": "light_turn_off",
                "arguments": '{"entity_id": "light.bedroom"}',
            }
        }
        
        result = await entity._execute_tool_call(tool_call)
        
        assert "Successfully turned off" in result
        assert "light.bedroom" in result

    @pytest.mark.asyncio
    async def test_execute_climate_set_temperature_success(self, mock_hass, mock_config_entry):
        """Test successful temperature setting."""
        mock_hass.services.async_call = AsyncMock()
        entity = OllamaConversationEntity(mock_hass, mock_config_entry)
        
        tool_call = {
            "function": {
                "name": "climate_set_temperature",
                "arguments": '{"entity_id": "climate.bedroom", "temperature": 72}',
            }
        }
        
        result = await entity._execute_tool_call(tool_call)
        
        assert "Successfully set" in result
        assert "climate.bedroom" in result
        assert "72" in result

    @pytest.mark.asyncio
    async def test_execute_climate_missing_temperature(self, mock_hass, mock_config_entry):
        """Test climate set temperature with missing temperature."""
        entity = OllamaConversationEntity(mock_hass, mock_config_entry)
        
        tool_call = {
            "function": {
                "name": "climate_set_temperature",
                "arguments": '{"entity_id": "climate.bedroom"}',
            }
        }
        
        result = await entity._execute_tool_call(tool_call)
        
        assert "Error" in result
        assert "requires entity_id and temperature" in result


# Integration test to verify the complete flow
@pytest.mark.asyncio
async def test_qwen3_light_control_flow(mock_hass, mock_config_entry):
    """Test complete flow: user request -> system prompt -> tool execution."""
    # Setup mocks
    mock_hass.services.async_call = AsyncMock()
    mock_client = AsyncMock()
    mock_hass.data = {
        "ollama_conversation": {
            "test_entry_123": mock_client,
        }
    }
    
    # Mock entity gathering
    with patch(
        "custom_components.ollama_conversation.conversation.async_get_exposed_entities"
    ) as mock_get_entities:
        mock_get_entities.return_value = {
            "light.kitchen": {
                "friendly_name": "Kitchen Light",
                "state": "off",
                "domain": "light",
            },
        }
        
        # Mock model response
        mock_client.chat = AsyncMock(
            return_value={
                "message": {
                    "content": "I have turned on the kitchen light for you.",
                    "role": "assistant",
                }
            }
        )
        
        entity = OllamaConversationEntity(mock_hass, mock_config_entry)
        
        # Create user input with all required parameters
        # ConversationInput requires: text, context, conversation_id, device_id, satellite_id, language, agent_id
        mock_context = MagicMock()
        user_input = ConversationInput(
            text="Turn on the kitchen light",
            context=mock_context,
            conversation_id=None,
            device_id=None,
            satellite_id=None,
            language="en",
            agent_id="test_agent",
        )
        
        # Process request
        result = await entity.async_process(user_input)
        
        # Verify system prompt was generated with entity context
        call_args = mock_client.chat.call_args
        messages = call_args[1]["messages"] if call_args else []
        
        # System prompt should be first message
        assert len(messages) > 0
        system_message = messages[0]
        assert system_message["role"] == "system"
        assert "light.kitchen" in system_message["content"]
        assert "Kitchen Light" in system_message["content"]
