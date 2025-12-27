"""Test suite for Ollama Conversation integration."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from aioresponses import aioresponses

from custom_components.ollama_conversation import async_setup_entry, async_unload_entry, OllamaClient
from custom_components.ollama_conversation.const import DOMAIN, CONF_MODEL, CONF_URL


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    hass.bus = Mock()
    hass.bus.async_listen_once = Mock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Ollama Test",
        data={
            CONF_URL: "http://localhost:11434",
            CONF_MODEL: "llama2",
        },
        source="user",
        entry_id="test_entry",
        unique_id="test_unique_id",
        discovery_keys={},
        options={},
        subentries_data={},
    )


class TestOllamaClient:
    """Test OllamaClient class."""

    @pytest.mark.asyncio
    async def test_get_models_success(self, mock_hass):
        """Test successful model retrieval."""
        with aioresponses() as m:
            m.get(
                "http://localhost:11434/api/tags",
                payload={
                    "models": [
                        {"name": "llama2"},
                        {"name": "mistral"}
                    ]
                }
            )
            
            client = OllamaClient(mock_hass, "http://localhost:11434")
            models = await client.get_models()
            
            assert len(models) == 2
            assert models[0]["name"] == "llama2"
            assert models[1]["name"] == "mistral"

    @pytest.mark.asyncio
    async def test_chat_request(self, mock_hass):
        """Test chat request."""
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/chat",
                payload={
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?"
                    }
                }
            )
            
            client = OllamaClient(mock_hass, "http://localhost:11434")
            messages = [{"role": "user", "content": "Hello"}]
            response = await client.chat(messages, "llama2")
            
            assert response["message"]["content"] == "Hello! How can I help you?"


class TestIntegrationSetup:
    """Test integration setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, mock_hass, mock_config_entry):
        """Test successful setup."""
        with aioresponses() as m:
            m.get(
                "http://localhost:11434/api/tags",
                payload={"models": [{"name": "llama2"}]}
            )
            
            mock_hass.config_entries = Mock()
            mock_hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
            
            result = await async_setup_entry(mock_hass, mock_config_entry)
            
            assert result is True
            assert DOMAIN in mock_hass.data
            assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_async_unload_entry(self, mock_hass, mock_config_entry):
        """Test successful unload."""
        mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: Mock()}
        mock_hass.config_entries = Mock()
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        
        result = await async_unload_entry(mock_hass, mock_config_entry)
        
        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]


def test_manifest_structure():
    """Test that manifest.json has required structure."""
    import json
    import os
    
    # Get the path to manifest.json relative to this test file
    test_dir = os.path.dirname(__file__)
    manifest_path = os.path.join(test_dir, "manifest.json")
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    assert manifest["domain"] == "ollama_conversation"
    assert "version" in manifest
    assert "requirements" in manifest
    assert any("ollama" in req for req in manifest["requirements"])


def test_constants_defined():
    """Test that all required constants are defined."""
    from custom_components.ollama_conversation.const import (
        DOMAIN,
        DEFAULT_URL,
        DEFAULT_TEMPERATURE,
        API_CHAT,
        API_TAGS,
    )
    
    assert DOMAIN == "ollama_conversation"
    assert DEFAULT_URL == "http://sanctuarymoon.local:11434"
    assert DEFAULT_TEMPERATURE == 0.7
    assert API_CHAT == "/api/chat"
    assert API_TAGS == "/api/tags"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
