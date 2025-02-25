import base64
from quart import request, Response
import hashlib
import secrets
from app.config.settings import load_config
import logging

def check_password(password):
    """Check if the provided password is valid.
    
    Args:
        password (str): The password to check
        
    Returns:
        bool: True if the password is valid, False otherwise
    """
    config = load_config()
    stored_password = config.get('admin_password', 'qaz654123')
    
    # In a production environment, use password hashing instead of plain text comparison
    return password == stored_password

def authenticate():
    """Send a 401 response that enables basic auth."""
    return Response(
        'Authentication required to access this resource.\n'
        'Please provide valid credentials', 
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

async def require_auth():
    """Verify authentication for protected routes.
    
    Returns:
        Response: Authentication failure response or None if authenticated
    """
    auth = request.headers.get('Authorization')
    if not auth:
        return authenticate()

    try:
        auth_type, auth_str = auth.split(' ', 1)
        if auth_type.lower() != 'basic':
            return authenticate()

        auth_str = base64.b64decode(auth_str).decode()
        username, password = auth_str.split(':', 1)
        
        if not check_password(password):
            logging.warning(f"Failed authentication attempt with username: {username}")
            return authenticate()
            
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return authenticate()
    
    return None

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