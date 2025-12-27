"""Conversation support for Ollama."""
import logging
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

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = OllamaConversationEntity(config_entry)
    async_add_entities([agent])


class OllamaConversationEntity(ConversationEntity):
    """Ollama conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the agent."""
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
        
        # System prompt
        system_prompt = self._build_system_prompt()
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
            _LOGGER.error("Error processing conversation: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I encountered an error: {str(err)}"
            )
            return ConversationResult(
                response=intent_response,
                conversation_id=user_input.conversation_id,
            )

    def _build_system_prompt(self) -> str:
        """Build the system prompt with Home Assistant context."""
        return """You are a helpful assistant integrated with Home Assistant.
You can control smart home devices and answer questions.
When asked to control devices, use the available tools to execute actions.
Always confirm actions and provide clear feedback to the user."""

    def _get_ha_tools(self) -> list[dict]:
        """Get available Home Assistant tools for the model."""
        tools = []
        
        # Light control
        tools.append({
            "type": "function",
            "function": {
                "name": "light_turn_on",
                "description": "Turn on a light or adjust its brightness/color",
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
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    arguments,
                    blocking=True,
                )
                return f"Successfully turned on {arguments.get('entity_id')}"

            elif function_name == "light_turn_off":
                await self.hass.services.async_call(
                    "light",
                    "turn_off",
                    arguments,
                    blocking=True,
                )
                return f"Successfully turned off {arguments.get('entity_id')}"

            elif function_name == "climate_set_temperature":
                await self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    arguments,
                    blocking=True,
                )
                return f"Successfully set temperature for {arguments.get('entity_id')} to {arguments.get('temperature')}"

            else:
                return f"Unknown function: {function_name}"

        except Exception as err:
            _LOGGER.error("Error executing tool call %s: %s", function_name, err)
            return f"Error executing {function_name}: {str(err)}"
