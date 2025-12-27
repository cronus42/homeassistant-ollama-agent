"""Test suite for Ollama Conversation integration."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.ollama_conversation import async_setup_entry, async_unload_entry, OllamaClient
from custom_components.ollama_conversation.const import DOMAIN, CONF_MODEL, CONF_URL


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Ollama Test",
        data={
            CONF_URL: "http://localhost:11434",
            CONF_MODEL: "llama2",
        },
        source="user",
        entry_id="test_entry",
    )


class TestOllamaClient:
    """Test OllamaClient class."""

    @pytest.mark.asyncio
    async def test_get_models_success(self, mock_hass):
        """Test successful model retrieval."""
        client = OllamaClient(mock_hass, "http://localhost:11434")
        
        with patch.object(client.session, "get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "models": [
                    {"name": "llama2"},
                    {"name": "mistral"}
                ]
            })
            mock_response.raise_for_status = Mock()
            mock_get.return_value.__aenter__.return_value = mock_response
            
            models = await client.get_models()
            assert len(models) == 2
            assert models[0]["name"] == "llama2"

    @pytest.mark.asyncio
    async def test_chat_request(self, mock_hass):
        """Test chat request."""
        client = OllamaClient(mock_hass, "http://localhost:11434")
        
        with patch.object(client.session, "post") as mock_post:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?"
                }
            })
            mock_response.raise_for_status = Mock()
            mock_post.return_value.__aenter__.return_value = mock_response
            
            messages = [{"role": "user", "content": "Hello"}]
            response = await client.chat(messages, "llama2")
            
            assert response["message"]["content"] == "Hello! How can I help you?"
            assert mock_post.called


class TestIntegrationSetup:
    """Test integration setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, mock_hass, mock_config_entry):
        """Test successful setup."""
        with patch("custom_components.ollama_conversation.OllamaClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_models = AsyncMock(return_value=[{"name": "llama2"}])
            
            mock_hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
            
            result = await async_setup_entry(mock_hass, mock_config_entry)
            
            assert result is True
            assert DOMAIN in mock_hass.data
            assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_async_unload_entry(self, mock_hass, mock_config_entry):
        """Test successful unload."""
        mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: Mock()}
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        
        result = await async_unload_entry(mock_hass, mock_config_entry)
        
        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]


def test_manifest_structure():
    """Test that manifest.json has required structure."""
    import json
    
    with open("manifest.json", "r") as f:
        manifest = json.load(f)
    
    assert manifest["domain"] == "ollama_conversation"
    assert "version" in manifest
    assert "requirements" in manifest
    assert "ollama" in manifest["requirements"][0]


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
