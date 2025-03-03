from quart import request

def get_api_key_from_request():
    """Extract Poe API key from request headers.
    
    Returns:
        str: The API key or None if not found
    """
    api_value = request.headers.get('Api-Key')
    auth_value = request.headers.get('Authorization')
    
    if api_value is not None:
        return api_value
    elif auth_value is not None and 'Bearer' in auth_value:
        return auth_value.split(' ')[1]
    
    return None