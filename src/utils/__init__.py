"""
Utility module initialization
"""
import os
import time
import logging
from datetime import datetime
from functools import wraps
from termcolor import colored

# Set up logging
def setup_logger():
    """Set up and configure the logger"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Configure logger
    logger = logging.getLogger('forex_trader')
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if this module gets imported more than once
    if logger.handlers:
        return logger

    # Create handler. Console output is handled separately via cprint
    # throughout the app, so only persist to file here to avoid duplicate
    # uncolored lines alongside every colored cprint message.
    log_file = os.path.join('logs', f'forex_trader_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

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


def call_with_retry(func, *args, max_attempts=3, base_delay=1, **kwargs):
    """
    Call a read-only/idempotent function with exponential backoff on failure.

    Only use this for calls that are safe to repeat (account/price/position
    lookups). Never use it for order placement or position-closing calls -
    if the first attempt actually succeeded but the response was lost to a
    network error, a retry would submit a duplicate order.
    """
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                log_warning(
                    f"{getattr(func, '__name__', 'call')} failed (attempt {attempt}/{max_attempts}): "
                    f"{e}. Retrying in {delay}s..."
                )
                time.sleep(delay)
    raise last_exception

# Export everything for easy imports
__all__ = ['logger', 'log_info', 'log_warning', 'log_error', 'log_success', 'log_trade', 'call_with_retry']
