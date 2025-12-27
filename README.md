# Home Assistant Ollama Conversation Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/yourusername/homeassistant-ollama-agent.svg)](https://github.com/yourusername/homeassistant-ollama-agent/releases)
[![License](https://img.shields.io/github/license/yourusername/homeassistant-ollama-agent.svg)](LICENSE)

A Home Assistant custom integration that provides conversation agent capabilities using Ollama with full tool/function calling support for device control.

## ✨ Features

- 🤖 **Local AI Processing**: Run language models locally via Ollama
- 🔧 **Tool/Function Calling**: Native support for Home Assistant device control
- 💡 **Smart Home Control**: Control lights, climate, and other devices through natural language
- 🔄 **Conversation History**: Maintains context across multiple turns
- ⚙️ **Configurable Parameters**: Adjust temperature, context window, and other model settings
- 🎯 **Optimized for Function-Capable Models**: Designed to work with tool-capable models like Home-FunctionGemma-270m

## 🚀 Quick Start

### Prerequisites

1. **Ollama Server**: Running locally or on your network
2. **Compatible Model**: Download a tool-capable model:
   ```bash
   ollama pull home-functiongemma-270m
   ```

### Installation via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add this repository URL
5. Search for "Ollama Conversation" and install
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ollama_conversation` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

### Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Ollama Conversation"**
4. Enter your Ollama server URL (default: `http://sanctuarymoon.local:11434`)
5. Select your model from the dropdown
6. Configure optional parameters (temperature, context window, etc.)

## 📖 Documentation

See the [detailed README](custom_components/ollama_conversation/README.md) for:
- Usage examples
- Supported device types
- Architecture details
- Troubleshooting guide
- API documentation

## 🆚 Comparison with Alternatives

### vs. home-llm Integration

| Feature | home-llm | ollama_conversation |
|---------|----------|---------------------|
| Ollama Support | ✅ Basic | ✅ Full API |
| Tool Calling | ❌ Limited | ✅ Native |
| UI Configuration | ❌ YAML only | ✅ Config Flow |
| Model Switching | ❌ Manual | ✅ Dropdown |
| Error Handling | ⚠️ Basic | ✅ Comprehensive |

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Credits

- Built by **goose** (Block's AI agent)
- Inspired by Home Assistant's `bedrock` integration
- Compatible with **Home-FunctionGemma-270m** model

## 🔒 Privacy

This integration processes everything locally. Your conversations never leave your network when using Ollama locally.

## 💬 Support

- 📖 [Documentation](custom_components/ollama_conversation/README.md)
- 🐛 [Issues](https://github.com/yourusername/homeassistant-ollama-agent/issues)
- 💬 [Home Assistant Community](https://community.home-assistant.io)
