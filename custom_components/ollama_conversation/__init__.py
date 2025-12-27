"""The Ollama Conversation integration."""
import logging
from typing import Literal

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_TAGS,
    CONF_MODEL,
    DOMAIN,
    TIMEOUT_LIST_MODELS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CONVERSATION]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ollama Conversation from a config entry."""
    url = entry.data[CONF_URL]
    
    # Validate connection
    client = OllamaClient(hass, url)
    try:
        await client.get_models()
    except Exception as err:
        _LOGGER.error("Failed to connect to Ollama server at %s: %s", url, err)
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class OllamaClient:
    """Client for Ollama API."""

    def __init__(self, hass: HomeAssistant, base_url: str) -> None:
        """Initialize the Ollama client."""
        self.hass = hass
        self.base_url = base_url.rstrip("/")
        self.session = async_get_clientsession(hass)

    async def get_models(self) -> list[dict]:
        """Get available models from Ollama."""
        url = f"{self.base_url}{API_TAGS}"
        
        try:
            async with async_timeout.timeout(TIMEOUT_LIST_MODELS):
                response = await self.session.get(url)
                response.raise_for_status()
                data = await response.json()
                return data.get("models", [])
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching models from %s: %s", url, err)
            raise
        except TimeoutError as err:
            _LOGGER.error("Timeout fetching models from %s", url)
            raise

    async def chat(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict:
        """Send chat request to Ollama."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            async with async_timeout.timeout(30):
                response = await self.session.post(url, json=payload)
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error in chat request: %s", err)
            raise
