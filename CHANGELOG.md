# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Qwen Tool Call Support**: Added support for Qwen2.5-coder's XML-based tool calling format
  - New parser function extracts tool calls from <tool_call> XML tags
  - Automatically converts Qwen format to standard tool_calls format
  - Added detection logic prioritizing Qwen format after standard format
  - Enhanced logging for Qwen tool call processing

### Fixed
- **Qwen2.5-coder Compatibility**: Qwen models now properly execute tool calls instead of outputting them as text
  - Resolves issue where tool calls appeared as JSON in conversation responses
  - Tool calls wrapped in XML tags are now parsed and executed correctly

## [1.1.0] - 2025-12-29

### Fixed
- **Gemma3 Think Block Issue**: Fixed issue where Gemma3 model responses were showing raw <think> blocks instead of user-facing text
  - Enhanced filter function to handle unclosed <think> tags
  - Added debug logging to track filtering operations
  - Implemented fallback responses when filtering results in empty text
  - System prompt now explicitly instructs models not to use <think> tags

### Added
- Smart fallback response generation when model output is filtered to empty
- Automatic action summaries (e.g., "Done! I've turned off light.desk_lamp")
- Enhanced debug logging for response processing pipeline
- Raw response logging before filtering (debug level)

### Changed
- System prompt updated with explicit "Response Format" section
- Prohibits use of <think> tags in model instructions
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
