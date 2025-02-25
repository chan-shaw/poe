from quart import Quart
from app.config.settings import load_config
from app.api.routes import register_routes
from app.errors.handlers import register_error_handlers

def create_app():
    """Create and configure the Quart application."""
    app = Quart(__name__)
    
    # Load configuration
    config = load_config()
    app.config.update(config)
    
    # Set up proxy if configured
    if 'http_proxy' in config and 'https_proxy' in config:
        import os
        os.environ["http_proxy"] = config['http_proxy']
        os.environ["https_proxy"] = config['https_proxy']
    
    # Register routes and error handlers
    register_routes(app)
    register_error_handlers(app)
    
    return app