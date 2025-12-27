# Home Assistant Ollama Conversation Integration

A Home Assistant integration that provides conversation agent capabilities using Ollama with full tool/function calling support for device control.

## Features

- 🤖 **Local AI Processing**: Run language models locally via Ollama
- 🔧 **Tool/Function Calling**: Native support for Home Assistant device control
- 💡 **Smart Home Control**: Control lights, climate, and other devices through natural language
- 🔄 **Conversation History**: Maintains context across multiple turns
- ⚙️ **Configurable Parameters**: Adjust temperature, context window, and other model settings
- 🎯 **Optimized for Home-FunctionGemma-270m**: Specifically designed to work with tool-capable models

## Why This Integration?

The existing `home-llm` integration doesn't properly support Ollama's tool calling API, which is essential for reliable device control. This integration implements:

- Proper Ollama tool/function calling format
- Structured device state representation
- Multi-turn tool execution
- Error handling and retry logic

## Installation

### Prerequisites

1. **Ollama Server**: Running at `http://sanctuarymoon.local:11434` (or your custom URL)
2. **Compatible Model**: Download a tool-capable model like Home-FunctionGemma-270m:
   ```bash
   ollama pull home-functiongemma-270m
   ```

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add this repository URL
5. Install "Ollama Conversation"
6. Restart Home Assistant

### Manual Installation

1. Copy the `homeassistant-ollama-agent` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Ollama Conversation"**
4. Enter your Ollama server URL (default: `http://sanctuarymoon.local:11434`)
5. Select your model from the dropdown (e.g., `Home-FunctionGemma-270m`)
6. Configure optional parameters:
   - **Temperature**: 0.0-2.0 (default: 0.7) - Controls randomness
   - **Context Window**: Token limit for conversation history (default: 8192)
   - **Top P**: 0.0-1.0 (default: 0.9) - Nucleus sampling threshold
   - **Top K**: Integer (default: 40) - Limits vocabulary for sampling

## Usage

### Basic Conversation

Once configured, the integration registers as a conversation agent. You can interact with it through:

- **Voice Assistants**: "Hey Assistant, turn on the living room lights"
- **Conversation Panel**: Type messages directly in the UI
- **Automations**: Trigger conversations programmatically

### Example Commands

```
"Turn on the kitchen lights"
"Set the thermostat to 72 degrees"
"What's the temperature in the bedroom?"
"Turn off all lights in the living room"
"Make the bedroom lights dimmer"
```

### Supported Device Types

Currently supported:
- ✅ Lights (on/off, brightness control)
- ✅ Climate devices (temperature control)

Coming soon:
- 🔜 Switches
- 🔜 Covers (blinds, garage doors)
- 🔜 Locks
- 🔜 Media players
- 🔜 Sensors (state queries)

## Architecture

### File Structure

```
homeassistant-ollama-agent/
├── manifest.json          # Integration metadata
├── __init__.py           # Entry point and OllamaClient
├── config_flow.py        # UI configuration flow
├── conversation.py       # Conversation agent entity
├── const.py             # Constants and defaults
└── strings.json         # UI translations
```

### Key Components

**OllamaClient** (`__init__.py`)
- Handles HTTP communication with Ollama API
- Methods: `get_models()`, `chat()`
- Connection validation and error handling

**OllamaConversationEntity** (`conversation.py`)
- Implements Home Assistant's `ConversationEntity`
- Manages conversation history
- Tool execution and result processing

**Tool Definitions**
- Converts Home Assistant services to Ollama function schema
- Validates parameters
- Executes service calls

### Tool Calling Flow

1. User sends message → `async_process()`
2. Build context: system prompt + history + user message
3. Get available tools from `_get_ha_tools()`
4. Send to Ollama with tools parameter
5. If tool calls in response:
   - Execute each tool via `_execute_tool_call()`
   - Append tool results to messages
   - Send back to Ollama for natural language response
6. Return final response to user

## Testing

Run the test suite:

```bash
python -m pytest test_integration.py -v
```

### Test Coverage

- ✅ OllamaClient methods (get_models, chat)
- ✅ Integration setup/teardown
- ✅ Manifest structure validation
- ✅ Constants verification

## Troubleshooting

### Connection Errors

**Error**: "Failed to connect to Ollama server"

**Solutions**:
- Verify Ollama is running: `ollama list`
- Check URL is correct (include port 11434)
- Test connection: `curl http://sanctuarymoon.local:11434/api/tags`

### No Models Found

**Error**: "No models found on the server"

**Solutions**:
- Pull a model: `ollama pull llama2`
- Verify models: `ollama list`
- Restart Ollama service

### Tool Calls Not Working

**Issues**: Model doesn't control devices

**Solutions**:
- Use a tool-capable model (e.g., Home-FunctionGemma-270m)
- Check Home Assistant logs for errors
- Verify entity IDs exist and are correct
- Ensure services are available (Developer Tools → Services)

## Comparison with home-llm

| Feature | home-llm | ollama_conversation |
|---------|----------|-------------------|
| Ollama Support | ✅ Basic | ✅ Full API |
| Tool Calling | ❌ Limited | ✅ Native |
| UI Configuration | ❌ YAML only | ✅ Config Flow |
| Model Switching | ❌ Manual | ✅ Dropdown |
| Error Handling | ⚠️ Basic | ✅ Comprehensive |
| Streaming | ❌ No | 🔜 Coming Soon |

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Credits

- Built by **goose** (Block's AI agent)
- Inspired by Home Assistant's `bedrock` integration
- Compatible with **Home-FunctionGemma-270m** model

## Support

- 📖 Documentation: [Home Assistant Docs](https://www.home-assistant.io)
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 Discussion: [Home Assistant Community](https://community.home-assistant.io)

---

**Note**: This integration is designed for local processing. Your conversations never leave your network when using Ollama locally.
