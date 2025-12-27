"""Constants for Ollama Conversation integration."""
DOMAIN = "ollama_conversation"
DEFAULT_NAME = "Ollama Conversation"

# Configuration
CONF_URL = "url"
CONF_MODEL = "model"
CONF_TEMPERATURE = "temperature"
CONF_CONTEXT_WINDOW = "context_window"
CONF_TOP_P = "top_p"
CONF_TOP_K = "top_k"

# Defaults
DEFAULT_URL = "http://sanctuarymoon.local:11434"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_CONTEXT_WINDOW = 8192
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 40

# API Endpoints
API_CHAT = "/api/chat"
API_TAGS = "/api/tags"
API_GENERATE = "/api/generate"

# Timeouts
TIMEOUT_CHAT = 30
TIMEOUT_LIST_MODELS = 5
