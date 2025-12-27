"""Config flow for Ollama Conversation integration."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_TAGS,
    CONF_CONTEXT_WINDOW,
    CONF_MODEL,
    CONF_TEMPERATURE,
    CONF_TOP_K,
    CONF_TOP_P,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    DEFAULT_TOP_P,
    DEFAULT_URL,
    DOMAIN,
    TIMEOUT_LIST_MODELS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, url: str) -> list[str]:
    """Validate the connection and return available models."""
    session = async_get_clientsession(hass)
    api_url = f"{url.rstrip('/')}{API_TAGS}"
    
    try:
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=TIMEOUT_LIST_MODELS)) as response:
            response.raise_for_status()
            data = await response.json()
            models = [model["name"] for model in data.get("models", [])]
            if not models:
                raise ValueError("No models found")
            return models
    except aiohttp.ClientError as err:
        _LOGGER.error("Connection failed: %s", err)
        raise
    except Exception as err:
        _LOGGER.error("Unexpected error: %s", err)
        raise


class OllamaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ollama Conversation."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.models: list[str] = []
        self.url: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.url = user_input[CONF_URL]
            
            try:
                self.models = await validate_connection(self.hass, self.url)
                return await self.async_step_model()
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "no_models"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=DEFAULT_URL): str,
                }
            ),
            errors=errors,
        )

    async def async_step_model(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle model selection."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Ollama ({user_input[CONF_MODEL]})",
                data={
                    CONF_URL: self.url,
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_TEMPERATURE: user_input.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                    CONF_CONTEXT_WINDOW: user_input.get(CONF_CONTEXT_WINDOW, DEFAULT_CONTEXT_WINDOW),
                    CONF_TOP_P: user_input.get(CONF_TOP_P, DEFAULT_TOP_P),
                    CONF_TOP_K: user_input.get(CONF_TOP_K, DEFAULT_TOP_K),
                },
            )

        return self.async_show_form(
            step_id="model",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL): vol.In(self.models),
                    vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): vol.All(
                        vol.Coerce(float), vol.Range(min=0.0, max=2.0)
                    ),
                    vol.Optional(CONF_CONTEXT_WINDOW, default=DEFAULT_CONTEXT_WINDOW): vol.Coerce(int),
                    vol.Optional(CONF_TOP_P, default=DEFAULT_TOP_P): vol.All(
                        vol.Coerce(float), vol.Range(min=0.0, max=1.0)
                    ),
                    vol.Optional(CONF_TOP_K, default=DEFAULT_TOP_K): vol.Coerce(int),
                }
            ),
        )
