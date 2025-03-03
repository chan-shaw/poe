import json
import time
import hashlib
import logging
import asyncio
from fastapi_poe.types import ProtocolMessage
from fastapi_poe.client import get_bot_response
from app.errors.handlers import ChatError

def is_valid_json(s):
    """Check if a string is valid JSON.
    
    Args:
        s (str): The string to check
        
    Returns:
        bool: True if the string is valid JSON, False otherwise
    """
    try:
        json.loads(s)
        return True
    except ValueError:
        return False

def yield_data(id, current_time, model, messages, s_type=None):
    """Format chat completion chunk data for streaming.
    
    Args:
        id (str): The completion ID
        current_time (int): Current timestamp
        model (str): Model name
        messages (str): Message content
        s_type (str, optional): Special chunk type. Defaults to None.
            
    Returns:
        str: Formatted SSE data
    """
    if s_type == "first":
        return f'data: {json.dumps({"id": id, "object": "chat.completion.chunk", "created": current_time, "model": model, "choices": [{"index": 0, "delta": {"role": "assistant", "content": messages}, "finish_reason": None}]})}\n\n'
    elif s_type == "finish":
        return f'data: {json.dumps({"id": id, "object": "chat.completion.chunk", "created": current_time, "model": model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\n\n'
    elif s_type == "end":
        return 'data: [DONE]\n\n'
    else:
        return f'data: {json.dumps({"id": id, "object": "chat.completion.chunk", "created": current_time, "model": model, "choices": [{"index": 0, "delta": {"content": messages}, "finish_reason": None}]})}\n\n'

async def get_chat_response(messages, bot_name, api_key, max_retries=3):
    """Get streaming chat response from Poe API with retry mechanism."""
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            async for partial in get_bot_response(messages=messages, bot_name=bot_name, api_key=api_key):
                raw_response = partial.raw_response
                response_text = raw_response['text']
                parsed_json = json.loads(response_text)
                text = parsed_json["text"]
                yield text
            return  # 成功完成，退出函数
        except Exception as e:
            last_error = e
            retry_count += 1
            logging.warning(f"Error in chat response (attempt {retry_count}/{max_retries}): {str(e)}")
            
            if retry_count < max_retries:
                # 指数退避策略
                await asyncio.sleep(2 ** retry_count)
            else:
                logging.error(f"Failed after {max_retries} attempts: {str(e)}")
                yield ChatError(str(e))
                return