import time
import logging
from quart import request, current_app
from functools import wraps

async def log_request(app):
    """记录请求信息的中间件"""
    @app.before_request
    async def before_request():
        request.start_time = time.time()
        
    @app.after_request
    async def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration': round(duration * 1000, 2),  # 毫秒
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
            
            # 根据状态码选择日志级别
            if response.status_code >= 500:
                logging.error(f"Request: {log_data}")
            elif response.status_code >= 400:
                logging.warning(f"Request: {log_data}")
            else:
                logging.info(f"Request: {log_data}")
                
        return response