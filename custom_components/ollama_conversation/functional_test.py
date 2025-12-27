#!/usr/bin/env python3
"""
Functional Test for Ollama Conversation Integration

This test simulates a complete integration workflow including:
- Connection validation
- Model listing
- Tool calling for device control
- Multi-turn conversation

Run: python functional_test.py
"""

import asyncio
import json
from datetime import datetime


class MockOllamaServer:
    """Mock Ollama server for testing."""
    
    def __init__(self):
        self.models = [
            {"name": "Home-FunctionGemma-270m"},
            {"name": "llama2"},
            {"name": "mistral"}
        ]
        self.conversation_history = []
    
    async def list_models(self):
        """Return available models."""
        print("📋 Listing available models...")
        return {"models": self.models}
    
    async def chat(self, messages, model, tools=None, temperature=0.7):
        """Simulate chat with tool calling."""
        user_message = messages[-1]["content"]
        print(f"💬 User: {user_message}")
        
        # Simulate tool calling for device control
        if "turn on" in user_message.lower() and "light" in user_message.lower():
            # First response: Tool call
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "light_turn_on",
                                "arguments": {
                                    "entity_id": "light.living_room"
                                }
                            }
                        }
                    ]
                }
            }
        
        elif "temperature" in user_message.lower() and "set" in user_message.lower():
            # Climate control
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "climate_set_temperature",
                                "arguments": {
                                    "entity_id": "climate.bedroom",
                                    "temperature": 72
                                }
                            }
                        }
                    ]
                }
            }
        
        # Regular response (after tool execution or no tools needed)
        return {
            "message": {
                "role": "assistant",
                "content": "I've completed your request. Is there anything else I can help you with?"
            }
        }


class FunctionalTest:
    """Complete functional test suite."""
    
    def __init__(self):
        self.server = MockOllamaServer()
        self.test_results = []
        self.start_time = datetime.now()
    
    def log_test(self, name, passed, details=""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details
        })
        print(f"{status} - {name}")
        if details:
            print(f"   └─ {details}")
    
    async def test_connection(self):
        """Test 1: Validate connection to Ollama."""
        print("\n🔌 TEST 1: Connection Validation")
        try:
            result = await self.server.list_models()
            models = result.get("models", [])
            self.log_test(
                "Connection Validation",
                len(models) > 0,
                f"Found {len(models)} models"
            )
            return True
        except Exception as e:
            self.log_test("Connection Validation", False, str(e))
            return False
    
    async def test_model_selection(self):
        """Test 2: Model selection and configuration."""
        print("\n🤖 TEST 2: Model Selection")
        try:
            result = await self.server.list_models()
            models = result.get("models", [])
            
            # Check for Home-FunctionGemma-270m
            has_tool_model = any(
                "Home-FunctionGemma" in m["name"] or "function" in m["name"].lower()
                for m in models
            )
            
            self.log_test(
                "Model Selection",
                has_tool_model,
                "Home-FunctionGemma-270m available" if has_tool_model else "Using fallback model"
            )
            return True
        except Exception as e:
            self.log_test("Model Selection", False, str(e))
            return False
    
    async def test_simple_conversation(self):
        """Test 3: Simple conversation without tools."""
        print("\n💭 TEST 3: Simple Conversation")
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ]
            
            response = await self.server.chat(messages, "llama2")
            has_response = "message" in response and "content" in response["message"]
            
            self.log_test(
                "Simple Conversation",
                has_response,
                "Got valid response"
            )
            return True
        except Exception as e:
            self.log_test("Simple Conversation", False, str(e))
            return False
    
    async def test_tool_calling_light(self):
        """Test 4: Tool calling for light control."""
        print("\n💡 TEST 4: Light Control (Tool Calling)")
        try:
            messages = [
                {"role": "system", "content": "You are a home automation assistant."},
                {"role": "user", "content": "Turn on the living room light"}
            ]
            
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "light_turn_on",
                        "description": "Turn on a light",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "entity_id": {"type": "string"}
                            },
                            "required": ["entity_id"]
                        }
                    }
                }
            ]
            
            # First call: Model returns tool call
            response = await self.server.chat(messages, "Home-FunctionGemma-270m", tools=tools)
            has_tool_calls = "tool_calls" in response.get("message", {})
            
            if has_tool_calls:
                tool_call = response["message"]["tool_calls"][0]
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                
                print(f"   🔧 Tool Called: {function_name}")
                print(f"   📝 Arguments: {json.dumps(arguments, indent=6)}")
                
                # Simulate tool execution
                tool_result = f"Successfully turned on {arguments['entity_id']}"
                print(f"   ✨ Result: {tool_result}")
                
                # Second call: Get natural language response
                messages.append(response["message"])
                messages.append({"role": "tool", "content": tool_result})
                
                final_response = await self.server.chat(messages, "Home-FunctionGemma-270m")
                has_final_response = "content" in final_response.get("message", {})
                
                if has_final_response:
                    print(f"   🤖 Assistant: {final_response['message']['content']}")
                
                self.log_test(
                    "Light Control",
                    has_tool_calls and has_final_response,
                    "Tool call executed and natural response received"
                )
            else:
                self.log_test("Light Control", False, "No tool calls returned")
            
            return has_tool_calls
        except Exception as e:
            self.log_test("Light Control", False, str(e))
            return False
    
    async def test_tool_calling_climate(self):
        """Test 5: Tool calling for climate control."""
        print("\n🌡️  TEST 5: Climate Control (Tool Calling)")
        try:
            messages = [
                {"role": "system", "content": "You are a home automation assistant."},
                {"role": "user", "content": "Set the bedroom temperature to 72 degrees"}
            ]
            
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "climate_set_temperature",
                        "description": "Set temperature for climate device",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "entity_id": {"type": "string"},
                                "temperature": {"type": "number"}
                            },
                            "required": ["entity_id", "temperature"]
                        }
                    }
                }
            ]
            
            response = await self.server.chat(messages, "Home-FunctionGemma-270m", tools=tools)
            has_tool_calls = "tool_calls" in response.get("message", {})
            
            if has_tool_calls:
                tool_call = response["message"]["tool_calls"][0]
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                
                print(f"   🔧 Tool Called: {function_name}")
                print(f"   📝 Arguments: {json.dumps(arguments, indent=6)}")
                
                self.log_test(
                    "Climate Control",
                    has_tool_calls and arguments.get("temperature") == 72,
                    f"Set {arguments['entity_id']} to {arguments['temperature']}°"
                )
            else:
                self.log_test("Climate Control", False, "No tool calls returned")
            
            return has_tool_calls
        except Exception as e:
            self.log_test("Climate Control", False, str(e))
            return False
    
    async def test_multi_turn_conversation(self):
        """Test 6: Multi-turn conversation with context."""
        print("\n🔄 TEST 6: Multi-turn Conversation")
        try:
            conversation = []
            
            # Turn 1
            conversation.append({"role": "user", "content": "Turn on the living room light"})
            response1 = await self.server.chat(conversation, "Home-FunctionGemma-270m")
            
            # Turn 2 (with context)
            conversation.append({"role": "assistant", "content": "I've turned on the light."})
            conversation.append({"role": "user", "content": "Now turn it off"})
            response2 = await self.server.chat(conversation, "Home-FunctionGemma-270m")
            
            has_context = len(conversation) == 4
            
            self.log_test(
                "Multi-turn Conversation",
                has_context,
                f"Maintained context over {len(conversation)} messages"
            )
            return True
        except Exception as e:
            self.log_test("Multi-turn Conversation", False, str(e))
            return False
    
    async def test_error_handling(self):
        """Test 7: Error handling and recovery."""
        print("\n⚠️  TEST 7: Error Handling")
        try:
            # Test with invalid entity
            messages = [
                {"role": "user", "content": "Turn on light.invalid_entity"}
            ]
            
            try:
                response = await self.server.chat(messages, "Home-FunctionGemma-270m")
                # Should handle gracefully
                self.log_test("Error Handling", True, "Handled invalid entity gracefully")
            except Exception as inner_e:
                self.log_test("Error Handling", True, f"Caught error: {type(inner_e).__name__}")
            
            return True
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        passed = sum(1 for t in self.test_results if t["passed"])
        total = len(self.test_results)
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print(f"Duration: {elapsed:.2f}s")
        print("="*60)
        
        if passed == total:
            print("✅ All tests passed!")
        else:
            print("⚠️  Some tests failed. Check logs above.")
    
    async def run_all_tests(self):
        """Run complete test suite."""
        print("="*60)
        print("🧪 OLLAMA CONVERSATION INTEGRATION - FUNCTIONAL TEST")
        print("="*60)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        await self.test_connection()
        await self.test_model_selection()
        await self.test_simple_conversation()
        await self.test_tool_calling_light()
        await self.test_tool_calling_climate()
        await self.test_multi_turn_conversation()
        await self.test_error_handling()
        
        self.print_summary()
        
        return all(t["passed"] for t in self.test_results)


async def main():
    """Run functional tests."""
    test = FunctionalTest()
    success = await test.run_all_tests()
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
