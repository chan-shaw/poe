import json
import time
import hashlib
import os
import logging
from quart import request, Response, stream_with_context, jsonify, make_response, send_from_directory, render_template
from fastapi_poe.types import ProtocolMessage

from app.auth.auth import get_api_key_from_request
from app.api.chat import get_chat_response, yield_data, is_valid_json
from app.config.settings import load_config
from app.errors.handlers import ChatError
from app.api.models import list_models, PoeError
from app.monitoring.metrics import get_metrics, track_request, track_model_usage

def register_routes(app):
    """Register API routes for the application."""
    
    @app.route('/', methods=['GET'])
    async def index():
        """渲染主页面，用于测试 Poe token 和模型列表健康度"""
        return await render_template('index.html')
    
    @app.route('/api/test-token', methods=['POST'])
    async def test_token():
        """测试 Poe token 是否有效，并返回可用模型列表"""
        try:
            data = await request.get_json()
            poe_api_key = data.get('token')
            
            if not poe_api_key:
                return await make_response(jsonify({
                    "success": False,
                    "message": "请提供 Poe API Token"
                }), 400)
            
            # 获取语言代码（如果有）
            language_code = data.get('language', 'en')
            
            # 调用 list_models 函数获取模型列表
            models_data = await list_models(poe_api_key, language_code)
            
            # 记录模型使用情况
            for model in models_data.get("data", []):
                track_model_usage(model.get("id"))
            
            return await make_response(jsonify({
                "success": True,
                "models": models_data.get("data", [])
            }))
            
        except Exception as e:
            logging.error(f"Token test error: {str(e)}")
            return await make_response(jsonify({
                "success": False,
                "message": f"测试失败: {str(e)}"
            }), 500)
    
    @app.route('/api/test-model', methods=['POST'])
    async def test_model():
        """测试单个模型的可用性"""
        try:
            data = await request.get_json()
            poe_api_key = data.get('token')
            model_id = data.get('model_id')
            
            if not poe_api_key or not model_id:
                return await make_response(jsonify({
                    "success": False,
                    "message": "请提供 Poe API Token 和模型 ID"
                }), 400)
            
            start_time = time.time()
            
            # 简单的测试消息
            test_message = ProtocolMessage(role="user", content="Hello")
            protocol_messages = [test_message]
            
            # 尝试获取响应
            response_text = ""
            async for response in get_chat_response(protocol_messages, model_id, poe_api_key):
                if isinstance(response, ChatError):
                    raise Exception(response.message)
                response_text += response
                if len(response_text) > 10:  # 只需要获取一小部分响应即可
                    break
            
            duration = time.time() - start_time
            
            # 记录指标
            track_request("POST", "test_model", 200, duration)
            track_model_usage(model_id)
            
            return await make_response(jsonify({
                "success": True,
                "model_id": model_id,
                "status": "healthy",
                "response": response_text[:50] + "..." if len(response_text) > 50 else response_text,
                "duration": round(duration, 2)
            }))
            
        except Exception as e:
            logging.error(f"Model test error: {str(e)}")
            return await make_response(jsonify({
                "success": False,
                "model_id": model_id,
                "status": "error",
                "message": str(e)
            }), 200)  # 返回200是为了前端能正常处理错误
    
    @app.route('/v1/models', methods=['GET'])
    async def get_models():
        """获取可用模型列表，格式与 OpenAI API 兼容"""
        try:
            # 从请求中获取 API key
            poe_api_key = get_api_key_from_request()
            if not poe_api_key:
                return await make_response('Invalid or missing Poe API Key', 401)
            
            # 获取语言代码（如果有）
            language_code = request.args.get('language', 'en')
            
            # 调用 list_models 函数获取模型列表
            models_data = await list_models(poe_api_key, language_code)
            
            # 创建响应并添加 CORS 头
            response = await make_response(jsonify(models_data))
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            return response
            
        except PoeError as e:
            logging.error(f"Error listing models: {str(e)}")
            error_response = {
                "error": {
                    "message": str(e),
                    "type": "api_error",
                    "param": None,
                    "code": "model_list_error"
                }
            }
            
            response = await make_response(jsonify(error_response), 400)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            return response
        except Exception as e:
            logging.error(f"Unexpected error in get_models: {str(e)}")
            error_response = {
                "error": {
                    "message": "An unexpected error occurred",
                    "type": "server_error",
                    "param": None,
                    "code": "server_error"
                }
            }
            
            response = await make_response(jsonify(error_response), 500)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            return response
    
    @app.route('/v1/chat/completions', methods=['OPTIONS', 'POST'])
    async def process_chat_completions():
        """Handle chat completions API endpoint."""
        if request.method == 'POST':
            # Verify content type
            if request.headers.get('Content-Type') != 'application/json':
                return await make_response('Invalid content type', 400)
            
            # Get Poe API key
            poe_api_key = get_api_key_from_request()
            if not poe_api_key:
                return await make_response('Invalid or missing Poe API Key', 401)
            
            # Process chat request
            data = await request.get_json()
            messages = data.get('messages')
            model = data.get('model')
            
            # Check if streaming is requested
            flow_status = data.get("stream", False)
            # Check if streaming is requested
            flow_status = data.get("stream", False)
            
            # 检查模型是否需要 replace_response 处理
            config = load_config()
            should_replace_response = False
            if "models" in config and model in config["models"]:
                should_replace_response = config["models"][model].get("replace_response", False)
            
            # Convert messages to Poe protocol format
            protocol_messages = []
            for message in messages:
                original_role = message["role"]
                # 根据不同角色进行转换
                if original_role == "assistant":
                    role = "bot"
                elif original_role == "developer":
                    role = "user"
                elif original_role == "system" and should_replace_response:
                    role = "user"
                else:
                    role = original_role
                content = message["content"]
                protocol_messages.append(
                    ProtocolMessage(role=role, content=content))
            
            # Log request info (sanitized)
            logging.info(f'Request Model Name: "{model}", Using API Key: "{poe_api_key[:4]}...{poe_api_key[-4:]}"')
            
            if flow_status:
                return await handle_streaming_response(protocol_messages, model, poe_api_key)
            else:
                return await handle_full_response(protocol_messages, model, poe_api_key)
                
        elif request.method == 'OPTIONS':
            config = load_config()
            allowed_origins = config.get('allowed_origins', ['*'])
            
            # Create an OPTIONS response with CORS headers
            response = await make_response("OK")
            response.headers["Content-Type"] = "text/plain; charset=utf-8"
            response.headers["vary"] = "Origin"
            response.headers["access-control-allow-methods"] = "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
            response.headers["access-control-max-age"] = "600"
            response.headers["access-control-allow-credentials"] = "true"
            
            # Set allowed origins based on config
            origin = request.headers.get('Origin')
            if origin and (origin in allowed_origins or '*' in allowed_origins):
                response.headers["access-control-allow-origin"] = origin
            else:
                response.headers["access-control-allow-origin"] = allowed_origins[0] if allowed_origins else "*"
                
            response.headers["access-control-allow-headers"] = "authorization,content-type,api-key"
            return response

    async def handle_streaming_response(protocol_messages, model, poe_api_key):
        """Handle streaming response for chat completions.
        
        Args:
            protocol_messages (list): List of protocol messages
            model (str): Model name
            poe_api_key (str): Poe API key
            
        Returns:
            Response: Streaming response
        """
        async def generate_flow_messages_async():
            current_time = int(time.time())
            full_hash = hashlib.md5(str(current_time).encode("utf-8")).hexdigest().upper()
            short_hash = full_hash[:29]
            id = "chatcmpl-" + short_hash
            
            out_status = False
            first_response = True
            output_tokens = 0  # 添加 token 计数
            input_tokens = sum(len(msg.content) // 4 for msg in protocol_messages)  # 估算输入 tokens
            
            async for response in get_chat_response(protocol_messages, model, poe_api_key):
                if isinstance(response, ChatError) and out_status == False:
                    error_message = {}
                    if is_valid_json(response.message):
                        error_message = json.loads(response.message)
                    else:
                        error_message = {"text": response.message}
                    
                    error_resp1 = "API request error, please check the following error message!"
                    error_resp2 = error_message["text"]

                    # Stream the error message
                    chunked_error_resp1 = list(error_resp1)
                    for chunk in chunked_error_resp1:
                        if first_response:
                            yield yield_data(id, current_time, model, chunk, "first")
                            first_response = False
                        else:
                            yield yield_data(id, current_time, model, chunk)

                    # Add code block for error
                    block_code1 = '\n```yaml\n'
                    yield yield_data(id, current_time, model, block_code1)
                    yield yield_data(id, current_time, model, error_resp2)

                    # Provide advice based on error message
                    block_code2 = '\n```\n'
                    advice_message = 'Solution: '
                    
                    if "Bot does not exist" in error_resp2:
                        advice = '1. The model you selected does not exist. Please try another available model.'
                    elif "run out of messages" in error_resp2:
                        advice = '1. You have consumed all available uses for this model with your current API key.\n2. If you have other API keys available, please try using them.'
                    elif "Internal server error" in error_resp2:
                        config = load_config()
                        api_url = config.get('api_url', 'https://api.example.com/keys')
                        advice = f'1. Your API key is invalid or expired. Please get a new key.\n2. Visit {api_url} to obtain a new API key using the same credentials as this site.'
                    else:
                        advice = '1. Please check your request parameters and try again.\n2. If the problem persists, please contact support.'

                    yield yield_data(id, current_time, model, block_code2)
                    yield yield_data(id, current_time, model, advice_message)
                    yield yield_data(id, current_time, model, block_code1)
                    yield yield_data(id, current_time, model, advice)
                    yield yield_data(id, current_time, model, block_code2)
                else:
                    out_status = True
                    if first_response:
                        yield yield_data(id, current_time, model, response, "first")
                        first_response = False
                    else:
                        yield yield_data(id, current_time, model, response)
                        
            # 在最后添加 usage 信息
            finish_data = json.loads(yield_data(id, current_time, model, "", "finish").replace('data: ', '').strip())
            finish_data["usage"] = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
            yield f'data: {json.dumps(finish_data)}\n\n'
            yield yield_data(id, current_time, model, "", "end")
            
        # Set headers for streaming response
        headers = {
            "Content-Type": "text/event-stream; charset=utf-8",
            "Connection": "close",
            "access-control-allow-origin": "*",
            "access-control-allow-credentials": "true",
            "access-control-expose-headers": "*",
        }
        
        return Response(
            generate_flow_messages_async(),
            mimetype='text/event-stream',
            headers=headers
        )

    async def handle_full_response(protocol_messages, model, poe_api_key):
        """Handle full (non-streaming) response for chat completions.
        
        Args:
            protocol_messages (list): List of protocol messages
            model (str): Model name
            poe_api_key (str): Poe API key
            
        Returns:
            Response: JSON response
        """
        current_time = int(time.time())
        full_hash = hashlib.md5(str(current_time).encode("utf-8")).hexdigest().upper()
        short_hash = full_hash[:29]
        id = "chatcmpl-" + short_hash

        content_string = ''
        output_tokens = 0  # 添加 token 计数
        input_tokens = sum(len(msg.content) // 4 for msg in protocol_messages)  # 估算输入 tokens

        try:
            async for response in get_chat_response(protocol_messages, model, poe_api_key):
                if isinstance(response, ChatError):
                    error_mes = ''
                    if is_valid_json(response.message):
                        error_message = json.loads(response.message)
                        error_mes = error_message.get("text")
                    else:
                        error_message = {"text": response.message}
                        error_mes = error_message.get("text")
                        
                    error_response = {
                        "error": {
                            "message": error_mes,
                            "type": "invalid_request_error",
                            "param": None,
                            "code": "invalid_request_error"
                        }
                    }
                    
                    # Create response with CORS headers
                    response = await make_response(jsonify(error_response))
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                    response.headers['Access-Control-Expose-Headers'] = '*'
                    
                    return response
                else:
                    content_string += response

            # Create success response
            responses = {
                "id": id,
                "object": "chat.completion",
                "created": current_time,
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content_string
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
            }

            # Create response with CORS headers
            response = await make_response(jsonify(responses))
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Expose-Headers'] = '*'
            
            return response
            
        except Exception as e:
            logging.error(f"Error in handle_full_response: {str(e)}")
            error_response = {
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "param": None,
                    "code": "server_error"
                }
            }
            
            response = await make_response(jsonify(error_response), 500)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            return response

    @app.route('/health', methods=['GET'])
    async def health_check():
        """健康检查端点"""
        return await make_response(jsonify({
            "status": "ok",
            "version": "1.0.0",
            "timestamp": int(time.time())
        }))
    @app.route('/metrics', methods=['GET'])
    async def metrics():
        """Prometheus 指标端点"""
        return Response(get_metrics(), mimetype='text/plain')
    
    # 在现有路由中添加指标跟踪
    @app.after_request
    async def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            endpoint = request.endpoint or 'unknown'
            track_request(request.method, endpoint, response.status_code, duration)
        return response
    @app.route('/favicon.ico')
    async def favicon():
        """Serve favicon."""
        return await send_from_directory(os.path.join(app.root_path, 'static'),
                              'favicon.ico', mimetype='image/vnd.microsoft.icon')