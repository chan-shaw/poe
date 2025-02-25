import time
import hashlib
import json

def generate_completion_id():
    """Generate a unique ID for a completion.
    
    Returns:
        str: Unique completion ID
    """
    current_time = int(time.time())
    full_hash = hashlib.md5(str(current_time).encode("utf-8")).hexdigest().upper()
    short_hash = full_hash[:29]
    return "chatcmpl-" + short_hash

def sanitize_api_key(api_key):
    """Sanitize API key for logging.
    
    Args:
        api_key (str): API key to sanitize
        
    Returns:
        str: Sanitized API key (first 4 chars + ... + last 4 chars)
    """
    if not api_key or len(api_key) < 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"

def safe_json_loads(json_str, default=None):
    """Safely load JSON string.
    
    Args:
        json_str (str): JSON string to load
        default (any, optional): Default value if JSON is invalid. Defaults to None.
        
    Returns:
        dict: Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (ValueError, TypeError):
        return default if default is not None else {}