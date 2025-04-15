"""
Utility module initialization
"""
import os
import logging
from datetime import datetime
from termcolor import colored

# Set up logging
def setup_logger():
    """Set up and configure the logger"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger('forex_trader')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    log_file = os.path.join('logs', f'forex_trader_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logger()

# Custom logging functions with color output
def log_info(message):
    """Log info message with color"""
    logger.info(message)
    
def log_warning(message):
    """Log warning message with color"""
    logger.warning(message)
    
def log_error(message):
    """Log error message with color"""
    logger.error(message)
    
def log_success(message):
    """Log success message with color"""
    logger.info(f"SUCCESS: {message}")
    
def log_trade(message):
    """Log trade-related message with color"""
    logger.info(f"TRADE: {message}")
    
# Export everything for easy imports
__all__ = ['logger', 'log_info', 'log_warning', 'log_error', 'log_success', 'log_trade']
