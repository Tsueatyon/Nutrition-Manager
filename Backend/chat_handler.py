# chat_handler.py - ULTRA-ROBUST VERSION
# Extensive error handling to prevent HTML error pages

import json
import sys
import configparser
from flask import Request
from flask_jwt_extended import get_jwt_identity
from mcp_tools import mcp
from functions import response
import inspect
import traceback

_config_path = None

def set_config_path(path):
    global _config_path
    _config_path = path

def get_config():
    config = configparser.ConfigParser()
    config_path = _config_path
    if not config_path and len(sys.argv) > 1:
        config_path = sys.argv[1]
    elif not config_path:
        import os
        if os.path.exists('config.dev.ini'):
            config_path = 'config.dev.ini'
        elif os.path.exists('../config.dev.ini'):
            config_path = '../config.dev.ini'
        else:
            config_path = 'config.dev.ini'
    
    if not config_path:
        raise ValueError("Config file path not set")
    
    config.read(config_path, encoding='utf-8')
    return config


def get_mcp_tools_for_llm():
    """Convert MCP tools to Anthropic function calling format."""
    tools = [
        {
            "name": "get_user_profile",
            "description": "Get current user's profile (age, sex, height, weight, activity, goal).",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "get_today_nutrition",
            "description": "Get today's calorie and macro totals.",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        },
        {
            "name": "calculate_daily_needs",
            "description": "Calculate estimated daily calorie and macro needs using Harris-Benedict formula.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sex": {"type": "string", "description": "Sex: 'male' or 'female'", "enum": ["male", "female"]},
                    "weight_kg": {"type": "number", "description": "Weight in kilograms"},
                    "height_cm": {"type": "number", "description": "Height in centimeters"},
                    "age": {"type": "integer", "description": "Age in years"},
                    "activity_level": {"type": "string", "description": "Activity level", "enum": ["sedentary", "light", "moderate", "active", "extra"]}
                },
                "required": ["sex", "weight_kg", "height_cm", "age", "activity_level"]
            }
        },
        {
            "name": "get_user_daily_needs",
            "description": "Get the current user's daily calorie and macro needs based on their profile.",
            "input_schema": {"type": "object", "properties": {}, "required": []}
        }
    ]
    return tools


def call_mcp_tool(tool_name: str, arguments: dict, username: str = None) -> str:
    try:
        from mcp_tools import get_user_profile, get_today_nutrition, calculate_daily_needs, get_user_daily_needs
        
        tool_map = {
            "get_user_profile": get_user_profile,
            "get_today_nutrition": get_today_nutrition,
            "calculate_daily_needs": calculate_daily_needs,
            "get_user_daily_needs": get_user_daily_needs
        }
        
        if tool_name not in tool_map:
            return json.dumps({"error": f"Tool {tool_name} not found"})
        
        tool_func = tool_map[tool_name]
        
        # Pass username to tools that need it
        if tool_name in ["get_user_profile", "get_today_nutrition", "get_user_daily_needs"]:
            if not arguments:
                arguments = {}
            arguments['username'] = username
        
        result = tool_func(**arguments) if arguments else tool_func()
        return result if isinstance(result, str) else json.dumps(result)
        
    except Exception as e:
        print(f"Tool execution error: {e}")
        traceback.print_exc()
        return json.dumps({"error": f"Tool execution error: {str(e)}"})


def handle_chat_message(request: Request):
    """Handle chat message with extensive error handling."""
    try:
        # Step 1: Authentication
        username = get_jwt_identity()
        if not username:
            return response(401, "Authentication required")
        
        # Step 2: Parse request body
        try:
            data = request.get_json()
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            return response(400, "Invalid JSON in request body")
        
        if not data:
            return response(400, "Empty request body")
        
        if 'message' not in data:
            return response(400, "Missing 'message' field in request body")
        
        # Step 3: Extract and validate message
        user_message = data.get('message')
        conversation_history = data.get('history', [])
        
        # Validate message
        if user_message is None:
            return response(400, "Message field cannot be null")
        
        if not isinstance(user_message, str):
            try:
                user_message = str(user_message)
            except:
                return response(400, "Message must be a string")
        
        if len(user_message.strip()) == 0:
            return response(400, "Message cannot be empty")
        
        # Validate history
        if not isinstance(conversation_history, list):
            print(f"Warning: history is not a list, got {type(conversation_history)}")
            conversation_history = []
        
        # Step 4: Get config
        try:
            cfg = get_config()
            llm_provider = cfg.get('llm', 'provider', fallback='anthropic').lower()
            api_key = cfg.get('llm', 'api_key', fallback='')
        except Exception as e:
            print(f"Config error: {e}")
            traceback.print_exc()
            return response(500, f"Configuration error: {str(e)}")
        
        if not api_key or api_key in ['YOUR_ANTHROPIC_API_KEY_HERE', 'YOUR_OPENAI_API_KEY_HERE']:
            return response(500, "LLM API key not configured")
        
        # Step 5: Build messages array
        try:
            tools = get_mcp_tools_for_llm()
            messages = []
            
            system_message = """You are a helpful nutrition coach assistant. You can help users with:
- Viewing their profile and nutrition goals
- Checking their daily nutrition intake
- Calculating their daily calorie and macro needs
- Providing nutrition advice based on their data

Use the available tools to get user information when needed. Be conversational and helpful."""
            
            messages.append({"role": "system", "content": system_message})
            
            # Process conversation history with extensive error handling
            for i, msg in enumerate(conversation_history[-10:]):
                try:
                    if not isinstance(msg, dict):
                        print(f"Warning: history[{i}] is not a dict, skipping")
                        continue
                    
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    
                    if not content:
                        print(f"Warning: history[{i}] has empty content, skipping")
                        continue
                    
                    if not isinstance(content, str):
                        print(f"Warning: history[{i}] content is not string, converting")
                        content = str(content)
                    
                    content = content.strip()
                    if len(content) > 0:
                        messages.append({"role": role, "content": content})
                    else:
                        print(f"Warning: history[{i}] content is empty after strip, skipping")
                        
                except Exception as e:
                    print(f"Error processing history[{i}]: {e}")
                    continue
            
            # Add current message
            messages.append({"role": "user", "content": user_message.strip()})
            
        except Exception as e:
            print(f"Error building messages: {e}")
            traceback.print_exc()
            return response(500, f"Error building messages: {str(e)}")
        
        # Step 6: Call LLM
        try:
            if llm_provider == 'anthropic':
                return call_anthropic_api(api_key, messages, tools, username)
            elif llm_provider == 'openai':
                return call_openai_api(api_key, messages, tools, username)
            else:
                return response(400, f"Unsupported LLM provider: {llm_provider}")
        except Exception as e:
            print(f"LLM call error: {e}")
            traceback.print_exc()
            return response(500, f"LLM error: {str(e)}")
            
    except Exception as e:
        # Catch-all error handler to prevent HTML error pages
        print(f"Unhandled chat error: {e}")
        traceback.print_exc()
        return response(500, f"Internal server error: {str(e)}")


def call_anthropic_api(api_key: str, messages: list, tools: list, username: str = None):
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        cfg = get_config()
        
        anthropic_messages = []
        system_content = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                content = msg.get("content", "")
                if content and isinstance(content, str) and len(content.strip()) > 0:
                    anthropic_messages.append({"role": msg["role"], "content": content.strip()})
        
        if len(anthropic_messages) == 0:
            return response(400, "No valid messages to process")
        
        max_iterations = 5
        iteration = 0
        tools_called = []
        
        while iteration < max_iterations:
            api_response = client.messages.create(
                model=cfg.get('llm', 'model', fallback='claude-3-5-haiku-20241022'),
                max_tokens=1024,
                system=system_content,
                messages=anthropic_messages,
                tools=tools if tools else None
            )
            
            assistant_content = []
            tool_use_blocks = []
            
            for content_block in api_response.content:
                if content_block.type == "text":
                    assistant_content.append(content_block.text)
                elif content_block.type == "tool_use":
                    tool_use_blocks.append(content_block)
            
            if assistant_content and not tool_use_blocks:
                return response(200, "Chat response generated", {
                    "message": " ".join(assistant_content),
                    "usage": {
                        "input_tokens": api_response.usage.input_tokens,
                        "output_tokens": api_response.usage.output_tokens
                    },
                    "tools_called": tools_called
                })
            
            if tool_use_blocks:
                assistant_message_content = []
                for block in tool_use_blocks:
                    assistant_message_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                
                anthropic_messages.append({"role": "assistant", "content": assistant_message_content})
                
                tool_results = []
                for block in tool_use_blocks:
                    tools_called.append({"name": block.name, "arguments": block.input})
                    tool_result = call_mcp_tool(block.name, block.input, username)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    })
                
                anthropic_messages.append({"role": "user", "content": tool_results})
                
                iteration += 1
                continue
            
            iteration += 1
        
        return response(500, "Max iterations reached in tool calling")
        
    except ImportError:
        return response(500, "Anthropic SDK not installed")
    except Exception as e:
        print(f"Anthropic API error: {e}")
        traceback.print_exc()
        return response(500, f"Anthropic API error: {str(e)}")


def call_openai_api(api_key: str, messages: list, tools: list, username: str = None):
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        cfg = get_config()
        
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        
        openai_messages = [msg for msg in messages if msg["role"] != "system"]
        
        max_iterations = 5
        iteration = 0
        tools_called = []
        
        while iteration < max_iterations:
            api_response = client.chat.completions.create(
                model=cfg.get('llm', 'model', fallback='gpt-4'),
                messages=openai_messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None
            )
            
            message = api_response.choices[0].message
            
            if message.tool_calls:
                openai_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [{"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in message.tool_calls]
                })
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tools_called.append({"name": tool_name, "arguments": tool_args})
                    tool_result = call_mcp_tool(tool_name, tool_args, username)
                    openai_messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": tool_name, "content": tool_result})
                
                iteration += 1
                continue
            
            if message.content:
                return response(200, "Chat response generated", {
                    "message": message.content,
                    "usage": {
                        "prompt_tokens": api_response.usage.prompt_tokens,
                        "completion_tokens": api_response.usage.completion_tokens,
                        "total_tokens": api_response.usage.total_tokens
                    },
                    "tools_called": tools_called
                })
            
            iteration += 1
        
        return response(500, "Max iterations reached")
        
    except ImportError:
        return response(500, "OpenAI SDK not installed")
    except Exception as e:
        print(f"OpenAI API error: {e}")
        traceback.print_exc()
        return response(500, f"OpenAI API error: {str(e)}")