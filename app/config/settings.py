import os
import yaml
import logging

def load_config():
    """Load configuration from config file."""
    config_file = os.environ.get('CONFIG_FILE', 'config/config.yaml')
    
    if not os.path.exists(config_file):
        # Create default config if it doesn't exist
        default_config = {
            'http_proxy': 'http://127.0.0.1:7897',
            'https_proxy': 'http://127.0.0.1:7897',
            'log_level': 'INFO',
            'log_file': 'logs/api.log',
            'allowed_origins': ['*'],  # CORS allowed origins
        }
        
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f)
        
        return default_config
    
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(config):
    """Set up logging configuration."""
    log_file = config.get('log_file', 'logs/api.log')
    log_level = config.get('log_level', 'INFO')
    
    # Create log directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, log_level))
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)