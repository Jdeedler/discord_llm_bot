"""
Logging utility for the Discord LLM Bot.
Configures logging for the application.
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger():
    """Configure and return a logger for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger('discord_llm_bot')
    logger.setLevel(logging.DEBUG)
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a file handler for debug logs
    debug_log_path = os.path.join(logs_dir, f'debug_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        debug_log_path, 
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Create a file handler for error logs
    error_log_path = os.path.join(logs_dir, f'error_{datetime.now().strftime("%Y%m%d")}.log')
    error_handler = RotatingFileHandler(
        error_log_path, 
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger
