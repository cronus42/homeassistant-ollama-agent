# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-12-29

### Fixed
- **Gemma3 Think Block Issue**: Fixed issue where Gemma3 model responses were showing raw `<think>` blocks instead of user-facing text
  - Enhanced `_filter_think_blocks()` to handle unclosed `<think>` tags
  - Added debug logging to track filtering operations
  - Implemented fallback responses when filtering results in empty text
  - System prompt now explicitly instructs models not to use `<think>` tags

### Added
- Smart fallback response generation when model output is filtered to empty
- Automatic action summaries (e.g., "Done! I've turned off light.desk_lamp")
- Enhanced debug logging for response processing pipeline
- Raw response logging before filtering (debug level)

### Changed
- System prompt updated with explicit "Response Format" section
- Prohibits use of `<think>` tags in model instructions
- More natural confirmation examples in system prompt

## [1.0.0] - 2024-01-XX

### Added
- Initial release with Ollama conversation agent
- Support for light control (on/off, brightness)
- Support for climate control (temperature setting)
- Standard Ollama tool calling format
- Gemma3-tools format compatibility
- Dynamic entity exposure
- Conversation history (10 messages)
- UI-based configuration flow
