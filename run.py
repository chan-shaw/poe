import os
import logging
from app import create_app
from app.config.settings import load_config, setup_logging

def main():
    # Load configuration
    config = load_config()
    
    # Set up logging
    setup_logging(config)
    
    # Create Flask app
    app = create_app()
    
    # Get port from config or use default
    port = config.get('port', 35555)
    
    logging.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()