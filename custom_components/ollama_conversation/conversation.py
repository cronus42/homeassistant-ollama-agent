"""Conversation support for Ollama."""
import logging
import re
import json
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
    Handles multiple blocks, unclosed tags, and various formatting variations.
    
    Args:
        text: The response text potentially containing think blocks
        
    Returns:
        The cleaned text with all think blocks removed
    """
    if not text:
        return text
    
    original_text = text
    
    # Pattern 1: Match complete <think>...</think> blocks (case-insensitive, with DOTALL flag)
    pattern_complete = r'<think>.*?</think>'
    text = re.sub(pattern_complete, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Pattern 2: Match unclosed <think> blocks (everything from <think> to end of string)
    pattern_unclosed = r'<think>.*$'
    text = re.sub(pattern_unclosed, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up any excess whitespace left behind
    text = re.sub(r'\n\s*\n+', '\n', text)
    text = text.strip()
    
    # Log if we filtered something out
    if text != original_text:
        _LOGGER.debug(
            "Filtered think blocks from response. Original length: %d, Filtered length: %d",
            len(original_text), len(text)
        )
        _LOGGER.debug("Original response: %s", original_text[:200])  # Log first 200 chars
        if text:
            _LOGGER.debug("Filtered response: %s", text[:200])
    
    return text


def _is_gemma3_tool_format(response: dict) -> bool:
    """Detect if response is in gemma3-tools format.
    
    Gemma3-tools format has:
    - A "type" field indicating the domain
    - Entity IDs as keys with action values
    - No "tool_calls" field
    
    Args:
        response: The response message dict
        
    Returns:
        True if response is gemma3-tools format, False otherwise
    """
    if not isinstance(response, dict):
        return False
    
    # Check for standard tool_calls format
    if "tool_calls" in response:
        return False
    
    # Check for gemma3-tools format markers
    has_type_field = "type" in response
    
    if not has_type_field:
        return False
    
    # Should have type and other keys that look like entity_ids
    type_val = response.get("type")
    if not isinstance(type_val, str):
        return False
    
    # Look for entity_id patterns (e.g., light.desk_lamp, climate.bedroom)
    for key in response.keys():
        if key != "type" and ("." in key or key in ["on", "off", "brightness"]):
            return True
    
    return False


def _parse_gemma3_tool_format(response: dict, domain_map: dict = None) -> list:
    """Parse gemma3-tools format and convert to standard tool_calls format.
    
    Gemma3-tools format example:
    {
        "type": "light",
        "light.desk_lamp": "on",
        "light.kitchen": {"brightness": 200}
    }
    
    Converts to standard format:
    [
        {
            "function": {
                "name": "light_turn_on",
                "arguments": {"entity_id": "light.desk_lamp"}
            }
        },
        ...
    ]
    
    Args:
        response: The gemma3-tools format response
        domain_map: Optional mapping of domain to action names (for future extensibility)
        
    Returns:
        List of tool_calls in standard format
    """
    tool_calls = []
    domain = response.get("type", "unknown")
    
    for key, value in response.items():
        if key == "type":
            continue
        
        # Skip special keys
        if key in ["__reasoning__", "text"]:
            continue
        
        # Parse entity ID and action
        entity_id = key if "." in key else f"{domain}.{key}"
        
        # Handle different action formats
        if isinstance(value, str):
            # Simple string action (e.g., "on", "off")
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
                # For climate, value should be a number (temperature)
                try:
                    temp = float(value)
                    tool_call = {
                        "function": {
                            "name": "climate_set_temperature",
                            "arguments": {"entity_id": entity_id, "temperature": temp}
                        }
                    }
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Could not parse climate temperature from: %s = %s",
                        entity_id, value
                    )
                    continue
            else:
                _LOGGER.warning("Unknown domain in gemma3 format: %s", domain)
                continue
                
        elif isinstance(value, dict):
            # Complex action with parameters (e.g., {"brightness": 200})
            if domain == "light":
                # Assume it's a light_turn_on with brightness
                tool_call = {
                    "function": {
                        "name": "light_turn_on",
                        "arguments": {
                            "entity_id": entity_id,
                            **value  # Include brightness and other params
                        }
                    }
                }
            elif domain == "climate":
                # Extract temperature if present
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
                    _LOGGER.warning(
                        "Climate action missing temperature: %s = %s",
                        entity_id, value
                    )
                    continue
            else:
                _LOGGER.warning("Unknown domain in gemma3 format: %s", domain)
                continue
        else:
            _LOGGER.warning(
                "Unexpected value type in gemma3 format: %s = %s (%s)",
                entity_id, value, type(value)
            )
            continue
        
        if "tool_call" in locals():
            tool_calls.append(tool_call)
    
    return tool_calls


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

            # Extract message content
            message_content = response.get("message", {})
            tool_calls = None
            
            # DEBUG: Log the full response to see what we got
            _LOGGER.debug("Full response from Ollama: %s", response)
            _LOGGER.debug("Message content keys: %s", list(message_content.keys()))
            
            # Handle tool calls - check for both standard and gemma3-tools formats
            if "tool_calls" in message_content:
                # Standard format
                tool_calls = message_content.get("tool_calls")
                _LOGGER.info("Detected standard tool call format: %s", tool_calls)
            elif _is_gemma3_tool_format(message_content):
                # Gemma3-tools format
                _LOGGER.info("Detected gemma3-tools format, converting...")
                tool_calls = _parse_gemma3_tool_format(message_content)
                if tool_calls:
                    _LOGGER.info("Converted %d gemma3-tools calls to standard format: %s", len(tool_calls), tool_calls)
            else:
                _LOGGER.warning("No tool calls detected in response. Content: %s", message_content.get("content", "")[:500])
            
            # Execute tool calls if any were found
            if tool_calls:
                _LOGGER.info("Executing %d tool calls", len(tool_calls))
                messages.append({
                    "role": "assistant",
                    "content": message_content.get("content", "")
                })
                
                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    tool_result = await self._execute_tool_call(tool_call)
                    tool_results.append(tool_result)
                    messages.append({
                        "role": "tool",
                        "content": str(tool_result),
                    })
                
                # Get final response after tool execution
                _LOGGER.debug("Requesting final response after tool execution")
                response = await client.chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                )
                
                raw_response = response.get("message", {}).get("content", "")
                _LOGGER.debug("Raw response from model: %s", raw_response[:200] if raw_response else "(empty)")

            response_text = response.get("message", {}).get("content", "")
            
            # Filter out think blocks before returning to user
            filtered_text = _filter_think_blocks(response_text)
            
            # If filtering resulted in empty response, provide a helpful default
            if not filtered_text or filtered_text.isspace():
                _LOGGER.warning(
                    "Response was empty after filtering think blocks. Original: %s",
                    response_text[:200] if response_text else "(empty)"
                )
                # If we executed tools, confirm the action
                if tool_calls:
                    # Build a simple confirmation based on what was executed
                    action_summaries = []
                    for tool_call in tool_calls:
                        func_name = tool_call.get("function", {}).get("name", "")
                        args = tool_call.get("function", {}).get("arguments", {})
                        entity_id = args.get("entity_id", "device")
                        
                        if func_name == "light_turn_on":
                            brightness = args.get("brightness")
                            if brightness:
                                action_summaries.append(f"turned on {entity_id} to {brightness} brightness")
                            else:
                                action_summaries.append(f"turned on {entity_id}")
                        elif func_name == "light_turn_off":
                            action_summaries.append(f"turned off {entity_id}")
                        elif func_name == "climate_set_temperature":
                            temp = args.get("temperature")
                            action_summaries.append(f"set {entity_id} to {temp}°")
                    
                    if action_summaries:
                        filtered_text = f"Done! I've {', and '.join(action_summaries)}."
                    else:
                        filtered_text = "Done! I've completed the requested action."
                else:
                    filtered_text = "I've processed your request."

            # Store conversation history
            conversation_id = user_input.conversation_id or ulid.ulid_now()
            if DOMAIN + "_conversations" not in self.hass.data:
                self.hass.data[f"{DOMAIN}_conversations"] = {}
            
            self.hass.data[f"{DOMAIN}_conversations"][conversation_id] = messages[-10:]  # Keep last 10 messages

            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(filtered_text)
            
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
6. After taking an action, provide a brief, natural confirmation to the user

**Response Format:**
- Do NOT use <think> tags or internal reasoning blocks in your responses
- Provide clear, concise responses directly to the user
- After executing a tool, simply confirm what was done (e.g., "I've turned off the desk lamp.")
- Keep confirmations brief and natural

**Example Interactions:**
- User: "Turn on the kitchen light" → You use light_turn_on with entity_id "light.kitchen" → You respond: "I've turned on the kitchen light."
- User: "Set the bedroom to 72 degrees" → You use climate_set_temperature with entity_id "climate.bedroom" and temperature 72 → You respond: "I've set the bedroom temperature to 72°."
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
