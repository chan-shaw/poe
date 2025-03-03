import requests
import logging

POE_GQL_URL = "https://poe.com/api/gql_POST"
POE_GQL_MODEL_HASH = "b24b2f2f6da147b3345eec1a433ed17b6e1332df97dea47622868f41078a40cc"

class PoeError(Exception):
    """自定义 Poe API 错误异常"""
    pass

async def list_models(api_key, language_code=None):
    """获取 Poe 平台上可用的模型列表
    
    Args:
        api_key (str): Poe API 密钥
        language_code (str, optional): 语言代码，例如 "en"、"zh"。默认为 None
        
    Returns:
        dict: 包含模型列表的字典，格式与 OpenAI API 兼容
        
    Raises:
        PoeError: 当 API 请求失败或返回空模型列表时
    """
    try:
        client = requests.Session()
        client.headers.update({
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://poe.com",
            "Referer": "https://poe.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "poegraphql": "1"
        })
        
        if language_code:
            client.headers.update({"Cookie": f"Poe-Language-Code={language_code}; p-b=1"})
        
        payload = {
            "queryName": "ExploreBotsListPaginationQuery",
            "variables": {
                "categoryName": "defaultCategory",
                "count": 150
            },
            "extensions": {
                "hash": POE_GQL_MODEL_HASH
            }
        }
        
        response = client.post(POE_GQL_URL, json=payload)
        
        if not response.ok:
            error_msg = f"API response error - Status code: {response.status_code}, Content: {response.text}"
            logging.error(error_msg)
            raise PoeError(error_msg)
        
        data = response.json()
        model_list = []
        
        edges = data.get("data", {}).get("exploreBotsConnection", {}).get("edges", [])
        for edge in edges:
            handle = edge.get("node", {}).get("handle")
            display_name = edge.get("node", {}).get("displayName", handle)
            if handle:
                model_list.append({
                    "id": handle,
                    "object": "model",
                    "created": 0,
                    "owned_by": "poe",
                    "name": display_name
                })
        
        if not model_list:
            raise PoeError("Model list is empty")
        
        # 返回 OpenAI 格式的响应
        return {
            "object": "list",
            "data": model_list
        }
        
    except Exception as e:
        if not isinstance(e, PoeError):
            logging.error(f"Error fetching model list: {str(e)}")
            raise PoeError(f"Failed to fetch model list: {str(e)}")
        raise