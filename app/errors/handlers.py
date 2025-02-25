import logging
from quart import jsonify

class ChatError(Exception):
    """Custom exception for chat-related errors."""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(ChatError)
    async def handle_chat_error(error):
        response = jsonify({
            'error': {
                'message': error.message,
                'type': 'chat_error',
                'code': error.status_code
            }
        })
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    async def handle_not_found(error):
        return jsonify({
            'error': {
                'message': 'The requested resource was not found',
                'type': 'not_found_error',
                'code': 404
            }
        }), 404
    
    @app.errorhandler(500)
    async def handle_server_error(error):
        logging.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': {
                'message': 'An internal server error occurred',
                'type': 'server_error',
                'code': 500
            }
        }), 500