from prometheus_client import Counter, Histogram, generate_latest
import time

# 定义指标
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP Requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 
    'HTTP Request Latency', 
    ['method', 'endpoint']
)

MODEL_USAGE = Counter(
    'model_usage_total',
    'Total Model Usage',
    ['model']
)

def track_request(method, endpoint, status, duration):
    """记录请求指标"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

def track_model_usage(model):
    """记录模型使用情况"""
    MODEL_USAGE.labels(model=model).inc()

def get_metrics():
    """获取所有指标"""
    return generate_latest()