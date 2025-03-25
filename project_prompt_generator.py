#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from logger_config import logger
from project_generator import ProjectPromptGenerator

if __name__ == "__main__":
    try:
        logger.info("=== PROJECT PROMPT GENERATOR SESSION START ===")
        logger.info(f"Session timestamp: {datetime.now().isoformat()}")
        generator = ProjectPromptGenerator()
        generator.run()
        logger.info("=== PROJECT PROMPT GENERATOR SESSION END ===")
    except ValueError as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        print("Please create a .env file in the project root with GEMINI_API_KEY=your_api_key")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"An unexpected error occurred: {str(e)}")
