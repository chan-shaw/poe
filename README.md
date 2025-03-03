# Poe to OpenAI API 代理

这个项目提供了一个将 Poe API 转换为 OpenAI API 格式的代理服务，使得支持 OpenAI API 的客户端可以无缝使用 Poe 的模型。

## 功能特点

- 完全兼容 OpenAI API 格式
- 支持流式响应
- 提供模型列表查询
- 内置模型健康检查
- 支持 CORS 跨域请求
- 内置速率限制保护

## 安装

1. 克隆仓库
```bash
git clone https://github.com/yourusername/poe2openai.git
cd poe2openai
```

2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```
## 配置
编辑 config/config.yaml 文件：
```yaml
http_proxy: http://127.0.0.1:7897  # 如果需要代理
https_proxy: http://127.0.0.1:7897
log_level: INFO
log_file: logs/api.log
allowed_origins: ['*']  # CORS 允许的源
port: 35555  # 服务端口
# admin_password: your_secure_password  # 管理员密码
```

## 运行
```bash
python run.py
```
服务将在 http://localhost:35555 上启动。

## API 使用

### 获取模型列表
```bash
curl -X GET "http://localhost:35555/v1/models" \
  -H "Authorization: Bearer YOUR_POE_API_KEY"
```

### 发送聊天请求
```bash
curl -X POST "http://localhost:35555/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_POE_API_KEY" \
  -d '{
    "model": "MODEL_ID",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ]
  }'
```

### 流式响应

```bash
curl -X POST "http://localhost:35555/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_POE_API_KEY" \
  -d '{
    "model": "MODEL_ID",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "stream": true
  }'
```

