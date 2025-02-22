from datetime import datetime
import logging.config
import json
import os


def setup_logging(
    default_path='config.json',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration"""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        
        # Ensure the logs directory exists
        log_dir = os.path.dirname(config['handlers']['file']['filename'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        config['handlers']['file']['filename'] = config['handlers']['file']['filename'].replace('%(date)', date_str)

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
