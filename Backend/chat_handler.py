import json
import os
import hashlib
from flask import Request
from flask_jwt_extended import get_jwt_identity
from functions import response
import traceback

from redis_client import cache_get, cache_set, get_cache_key_for_recommendation, get_cache_key_for_chat


try:
    from celery_app import process_llm_message
except ImportError:
    process_llm_message = None


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
            "description": "Calculate estimated daily calorie and macro needs using Harris-Benedict formula. Takes into account activity level and goal (cut/maintain/bulk).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sex": {"type": "string", "description": "Sex: 'male' or 'female'", "enum": ["male", "female"]},
                    "weight_kg": {"type": "number", "description": "Weight in kilograms"},
                    "height_cm": {"type": "number", "description": "Height in centimeters"},
                    "age": {"type": "integer", "description": "Age in years"},
                    "activity_level": {"type": "string", "description": "Activity level", "enum": ["sedentary", "light", "moderate", "active", "extra"]},
                    "goal": {"type": "string", "description": "Goal: 'cut' for weight loss, 'maintain' for maintenance, 'bulk' for weight gain", "enum": ["cut", "maintain", "bulk"]}
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
            llm_provider = os.getenv('LLM_PROVIDER', 'anthropic').lower()
            api_key = os.getenv('ANTHROPIC_API_KEY')
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
        
        # Step 6: Check cache for similar recommendations
        query_hash = hashlib.md5(user_message.strip().lower().encode()).hexdigest()
        cache_key = get_cache_key_for_recommendation(username, query_hash)
        cached_response = cache_get(cache_key)
        
        if cached_response:
            print(f"Cache hit for query: {user_message[:50]}...")
            return response(200, "Cached recommendation", cached_response)
        
        # Step 7: Store chat history in Redis
        try:
            chat_key = get_cache_key_for_chat(username)
            chat_history = conversation_history + [{"role": "user", "content": user_message.strip()}]
            cache_set(chat_key, chat_history, ttl=86400 * 7)
        except Exception as e:
            print(f"Failed to cache chat history: {e}")
        
        # Step 8: Process LLM call in background
        try:
            use_background = os.getenv('USE_BACKGROUND_JOBS', 'false').lower() == 'true'
            
            if use_background and process_llm_message:
                try:
                    task = process_llm_message.delay(api_key, messages, tools, username, llm_provider)
                    return response(202, "Request accepted, processing in background", {
                        "task_id": task.id,
                        "status": "processing",
                        "message": "Your request is being processed. Please check back in a moment."
                    })
                except Exception as e:
                    print(f"Failed to start background task: {e}. Falling back to sync.")
                    use_background = False
            
            if not use_background:
                # Fallback to synchronous processing
                if llm_provider == 'anthropic':
                    result = call_anthropic_api(api_key, messages, tools, username)
                else:
                    return response(400, f"Unsupported LLM provider: {llm_provider}")
                
                # Handle result (can be dict with error or success data)
                if isinstance(result, dict):
                    if "error" in result:
                        return response(500, result["error"])
                    else:
                        # Cache successful responses
                        cache_set(cache_key, result, ttl=3600)
                        # Update chat history with AI response
                        try:
                            chat_key = get_cache_key_for_chat(username)
                            updated_history = chat_history + [{"role": "assistant", "content": result.get("message", "")}]
                            cache_set(chat_key, updated_history, ttl=86400 * 7)  # 7 days
                        except Exception as e:
                            print(f"Failed to update chat history with AI response: {e}")
                        return response(200, "Chat response generated", result)
                else:
                    # Legacy response object
                    if result.status_code == 200:
                        try:
                            result_data = json.loads(result.get_data(as_text=True))
                            if result_data.get('code') == 200:
                                cache_set(cache_key, result_data.get('data', {}), ttl=3600)
                        except:
                            pass
                    return result
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
    """Call Anthropic API with improved error handling."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
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
            return {"error": "No valid messages to process"}
        
        max_iterations = 5
        iteration = 0
        tools_called = []
        
        while iteration < max_iterations:
            try:
                api_response = client.messages.create(
                    model=os.getenv('LLM_MODEL', 'claude-3-5-haiku-20241022'),
                    max_tokens=1024,
                    system=system_content,
                    messages=anthropic_messages,
                    tools=tools if tools else None,
                    timeout=30.0
                )
            except anthropic.APIError as e:
                error_msg = f"Anthropic API error: {e.status_code} - {e.message}"
                print(error_msg)
                return {"error": error_msg}
            except anthropic.APIConnectionError as e:
                error_msg = f"Anthropic connection error: {str(e)}"
                print(error_msg)
                return {"error": error_msg}
            except anthropic.APITimeoutError as e:
                error_msg = f"Anthropic timeout error: {str(e)}"
                print(error_msg)
                return {"error": error_msg}
            except Exception as e:
                error_msg = f"Unexpected Anthropic error: {str(e)}"
                print(error_msg)
                traceback.print_exc()
                return {"error": error_msg}
            
            assistant_content = []
            tool_use_blocks = []
            
            for content_block in api_response.content:
                if content_block.type == "text":
                    assistant_content.append(content_block.text)
                elif content_block.type == "tool_use":
                    tool_use_blocks.append(content_block)
            
            if assistant_content and not tool_use_blocks:
                return {
                    "message": " ".join(assistant_content),
                    "usage": {
                        "input_tokens": api_response.usage.input_tokens,
                        "output_tokens": api_response.usage.output_tokens
                    },
                    "tools_called": tools_called
                }
            
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
                    try:
                        tool_result = call_mcp_tool(block.name, block.input, username)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result
                        })
                    except Exception as e:
                        print(f"Tool execution error: {e}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps({"error": f"Tool execution failed: {str(e)}"})
                        })
                
                anthropic_messages.append({"role": "user", "content": tool_results})
                
                iteration += 1
                continue
            
            iteration += 1
        
        return {"error": "Max iterations reached in tool calling"}
        
    except ImportError:
        return {"error": "Anthropic SDK not installed"}
    except Exception as e:
        error_msg = f"Anthropic API error: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return {"error": error_msg}


