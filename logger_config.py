import logging
from datetime import datetime

# Set up logging
LOG_FILE = "project_prompt_generator.log"

def setup_logger():
    """Configure and return a logger for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    logger = logging.getLogger("ProjectPromptGenerator")
    return logger

logger = setup_logger()