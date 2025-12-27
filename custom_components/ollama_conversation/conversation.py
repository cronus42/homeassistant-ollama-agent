"""Conversation support for Ollama."""
import logging
import re
from typing import Any, Literal
import json

from homeassistant.components import conversation
from homeassistant.components.conversation import ConversationEntity, ConversationInput, ConversationResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import (
    CONF_CONTEXT_WINDOW,
    CONF_MODEL,
    CONF_TEMPERATURE,
    DOMAIN,
)
from .helpers import async_get_exposed_entities, format_entities_for_prompt

_LOGGER = logging.getLogger(__name__)


def _filter_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks from response text.
    
    This filters out internal reasoning blocks that should not be shown to users.
    Handles multiple blocks and various formatting variations.
    
    Args:
        text: The response text potentially containing think blocks
        
    Returns:
        The cleaned text with all think blocks removed
    """
    if not text:
        return text
    
    # Pattern to match <think>...</think> blocks (case-insensitive, with DOTALL flag)
    # This handles:
    # - Multiple think blocks in one response
    # - Newlines and multi-line content within blocks
    # - Whitespace variations
    pattern = r'<think>.*?</think>'
    
    # Remove all think blocks
    cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up any excess whitespace left behind
    # Replace multiple newlines with a single newline, then strip leading/trailing whitespace
    cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = OllamaConversationEntity(hass, config_entry)
    async_add_entities([agent])


class OllamaConversationEntity(ConversationEntity):
    """Ollama conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Ollama ({entry.data[CONF_MODEL]})",
            "manufacturer": "Ollama",
            "model": entry.data[CONF_MODEL],
        }

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return MATCH_ALL

    @property
    def supported_features(self) -> conversation.ConversationEntityFeature:
        """Return supported features."""
        return conversation.ConversationEntityFeature.CONTROL

    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Process a sentence."""
        client = self.hass.data[DOMAIN][self.entry.entry_id]
        model = self.entry.data[CONF_MODEL]
        temperature = self.entry.data.get(CONF_TEMPERATURE, 0.7)

        # Build conversation history
        messages = []
        
        # System prompt with entity context (now async!)
        system_prompt = await self._build_system_prompt()
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if available
        if user_input.conversation_id:
            conversation_data = self.hass.data.get(f"{DOMAIN}_conversations", {})
            history = conversation_data.get(user_input.conversation_id, [])
            messages.extend(history)
        
        # Add user message
        messages.append({"role": "user", "content": user_input.text})

        # Get available tools
        tools = self._get_ha_tools()

        try:
            # Send to Ollama
            response = await client.chat(
                messages=messages,
                model=model,
                tools=tools,
                temperature=temperature,
            )

            # Handle tool calls if present
            if "message" in response and response["message"].get("tool_calls"):
                tool_calls = response["message"]["tool_calls"]
                messages.append(response["message"])
                
                # Execute tool calls
                for tool_call in tool_calls:
                    tool_result = await self._execute_tool_call(tool_call)
                    messages.append({
                        "role": "tool",
                        "content": str(tool_result),
                    })
                
                # Get final response after tool execution
                response = await client.chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                )

            response_text = response.get("message", {}).get("content", "I'm sorry, I couldn't process that.")
            
            # Filter out think blocks before returning to user
            response_text = _filter_think_blocks(response_text)

            # Store conversation history
            conversation_id = user_input.conversation_id or ulid.ulid_now()
            if DOMAIN + "_conversations" not in self.hass.data:
                self.hass.data[f"{DOMAIN}_conversations"] = {}
            
            self.hass.data[f"{DOMAIN}_conversations"][conversation_id] = messages[-10:]  # Keep last 10 messages

            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(response_text)
            
            return ConversationResult(
                response=intent_response,
                conversation_id=conversation_id,
            )

        except Exception as err:
            _LOGGER.exception("Error processing conversation: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I encountered an error: {str(err)}"
            )
            return ConversationResult(
                response=intent_response,
                conversation_id=user_input.conversation_id,
            )

    async def _build_system_prompt(self) -> str:
        """Build the system prompt with Home Assistant entity context.
        
        This dynamically includes:
        - List of available devices and their current states
        - Information about device locations (areas)
        - Specific instructions for tool usage
        """
        # Get all exposed entities
        entities = await async_get_exposed_entities(self.hass)
        formatted_entities = format_entities_for_prompt(entities)
        
        system_prompt = f"""You are a helpful Home Assistant assistant that can control smart home devices.

{formatted_entities}

**Your Capabilities:**
You can interact with the devices listed above using these tools:
- light_turn_on: Turn on a light or adjust brightness
- light_turn_off: Turn off a light
- climate_set_temperature: Set target temperature for climate devices

**Important Instructions:**
1. Always use the EXACT entity_id when calling tools (e.g., light.living_room, not "living room light")
2. Entity IDs use the format: domain.device_name (e.g., light.kitchen, climate.bedroom)
3. When the user refers to a device by name, find the matching entity_id from the list above
4. If a device name is ambiguous or not found, ask the user for clarification
5. Always confirm what action you're performing before executing
6. After taking an action, report what was done

**Example Interactions:**
- User: "Turn on the kitchen light" → You use light_turn_on with entity_id "light.kitchen"
- User: "Set the bedroom to 72 degrees" → You use climate_set_temperature with entity_id "climate.bedroom" and temperature 72
- User: "Turn off all lights" → You ask which lights since there are multiple, or turn off each one separately

Now respond helpfully to the user's request."""

        return system_prompt

    def _get_ha_tools(self) -> list[dict]:
        """Get available Home Assistant tools for the model."""
        tools = []
        
        # Light control
        tools.append({
            "type": "function",
            "function": {
                "name": "light_turn_on",
                "description": "Turn on a light or adjust its brightness",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The entity ID of the light (e.g., light.living_room)"
                        },
                        "brightness": {
                            "type": "integer",
                            "description": "Brightness level (0-255)",
                            "minimum": 0,
                            "maximum": 255
                        }
                    },
                    "required": ["entity_id"]
                }
            }
        })
        
        tools.append({
            "type": "function",
            "function": {
                "name": "light_turn_off",
                "description": "Turn off a light",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The entity ID of the light"
                        }
                    },
                    "required": ["entity_id"]
                }
            }
        })

        # Climate control
        tools.append({
            "type": "function",
            "function": {
                "name": "climate_set_temperature",
                "description": "Set the temperature for a climate device",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The entity ID of the climate device"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Target temperature"
                        }
                    },
                    "required": ["entity_id", "temperature"]
                }
            }
        })

        return tools

    async def _execute_tool_call(self, tool_call: dict) -> str:
        """Execute a tool call and return the result."""
        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"].get("arguments", {})
        
        # Parse arguments if they're a string
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                _LOGGER.error("Failed to parse tool arguments: %s", arguments)
                return f"Error: Invalid arguments format"

        try:
            if function_name == "light_turn_on":
                entity_id = arguments.get("entity_id")
                brightness = arguments.get("brightness")
                
                if not entity_id:
                    return "Error: light_turn_on requires entity_id parameter"
                
                service_data = {"entity_id": entity_id}
                if brightness is not None:
                    service_data["brightness"] = brightness
                
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    service_data,
                    blocking=True,
                )
                
                if brightness is not None:
                    return f"Successfully turned on {entity_id} to {brightness} brightness"
                return f"Successfully turned on {entity_id}"

            elif function_name == "light_turn_off":
                entity_id = arguments.get("entity_id")
                
                if not entity_id:
                    return "Error: light_turn_off requires entity_id parameter"
                
                await self.hass.services.async_call(
                    "light",
                    "turn_off",
                    {"entity_id": entity_id},
                    blocking=True,
                )
                return f"Successfully turned off {entity_id}"

            elif function_name == "climate_set_temperature":
                entity_id = arguments.get("entity_id")
                temperature = arguments.get("temperature")
                
                if not entity_id or temperature is None:
                    return "Error: climate_set_temperature requires entity_id and temperature"
                
                await self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {"entity_id": entity_id, "temperature": temperature},
                    blocking=True,
                )
                return f"Successfully set {entity_id} to {temperature}°"

            else:
                return f"Unknown function: {function_name}"

        except Exception as err:
            _LOGGER.error("Error executing tool call %s: %s", function_name, err)
            return f"Error executing {function_name}: {str(err)}"
