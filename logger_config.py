import logging
import os
from datetime import datetime

# Create a time-based log directory structure
current_date = datetime.now().strftime("%Y-%m-%d")
log_base_dir = os.path.join(os.getcwd(), "log")
date_log_dir = os.path.join(log_base_dir, current_date)

# Create directory with timestamp to separate each run
run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
run_log_dir = os.path.join(date_log_dir, run_timestamp)
os.makedirs(run_log_dir, exist_ok=True)

# Define log file path
LOG_FILE = os.path.join(run_log_dir, "project_prompt_generator.log")

# Define debug API calls directory
DEBUG_API_CALLS_DIR = os.path.join(run_log_dir, "debug_ai_calls")

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
    
    # Log the directory structure for debugging
    logger.info(f"Log file created at: {LOG_FILE}")
    logger.info(f"Debug API calls will be stored in: {DEBUG_API_CALLS_DIR}")
    
    return logger

logger = setup_logger()