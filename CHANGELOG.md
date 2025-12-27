# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-12-27

### Fixed
- **Bug #1**: Fixed 500 Internal Server Error when conversing with assistant
  - Added better error handling and logging in chat API calls
  - Increased timeout from 30s to 60s for tool-heavy conversations
  - Added detailed debug logging to diagnose API issues
  - Fixed response parsing to handle edge cases
- **Bug #2**: Fixed "This assistant cannot control your home" warning
  - Added `supported_features` property returning `ConversationEntityFeature.CONTROL`
  - Integration now properly declares device control capabilities to Home Assistant

### Changed
- Improved error messages with more descriptive information
- Added `async_set_speech()` call to properly set response text in intent
- Enhanced tool argument parsing to handle both dict and string formats
- Better exception handling with user-friendly error messages

### Improved
- More comprehensive logging throughout the integration
- Better JSON parsing error handling
- Response status validation before parsing

## [1.0.0] - 2025-12-26

### Added
- Initial release of Ollama Conversation integration
- Full Ollama API support with tool/function calling
- UI-based configuration flow
- Support for light control (on/off, brightness)
- Support for climate control (temperature setting)
- Conversation history management (last 10 messages)
- Configurable parameters (temperature, context_window, top_p, top_k)
- Comprehensive error handling
- Model selection dropdown
- Connection validation
- Unit tests and functional tests
- Complete documentation

### Features
- Local AI processing via Ollama
- Natural language device control
- Multi-turn conversation support
- Tool execution with result feedback
- Home Assistant service integration
- HACS compatibility

### Documentation
- Detailed README with usage examples
- Implementation summary
- Troubleshooting guide
- Architecture documentation
- API endpoint documentation
