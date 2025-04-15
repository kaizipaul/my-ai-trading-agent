"""
Configuration settings for the trading system
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Trading symbols configuration - load from environment or use defaults
def get_symbols_from_env():
    """Get trading symbols from environment variable or use defaults"""
    symbols_str = os.getenv('SYMBOLS', 'EUR/USD,GBP/USD,USD/JPY,XAU/USD,AAPL,MSFT,GOOG')
    return [s.strip() for s in symbols_str.split(',')]

# Get timeframes from environment or use defaults
def get_timeframes_from_env():
    """Get timeframes from environment variable or use defaults"""
    timeframes_str = os.getenv('TIMEFRAMES', '1h,4h,1d')
    return [t.strip() for t in timeframes_str.split(',')]

# Trading symbols
FOREX_PAIRS = get_symbols_from_env()

# Timeframes to analyze
TIMEFRAMES = get_timeframes_from_env()

# Risk management parameters
MAX_POSITION_SIZE = float(os.getenv('MAX_RISK_PER_TRADE', 0.02))  # 2% per trade
STOP_LOSS_PIPS = 50
TAKE_PROFIT_PIPS = 100
MAX_DAILY_LOSS = 0.05  # 5% max daily loss
MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', 3))

# Technical indicators configuration
MOVING_AVERAGES = [20, 50, 200]
RSI_PERIOD = 14
MACD_SETTINGS = {
    'fast': 12,
    'slow': 26,
    'signal': 9
}

# Strategy params
STRATEGY_MIN_CONFIDENCE = 0.7
AI_MODEL = "claude-3-sonnet-20240229"
AI_MAX_TOKENS = 4096
AI_TEMPERATURE = 0.7

# System settings
SLEEP_BETWEEN_RUNS_MINUTES = int(os.getenv('SLEEP_BETWEEN_RUNS_MINUTES', 5))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'True').lower() in ('true', '1', 't')

# Alpaca Markets Trade Execution settings
EXECUTE_TRADES = os.getenv('EXECUTE_TRADES', 'False').lower() in ('true', '1', 't')
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '')
ALPACA_API_SECRET = os.getenv('ALPACA_API_SECRET', '')
ALPACA_API_URL = os.getenv('ALPACA_API_URL', 'https://paper-api.alpaca.markets')  # Paper trading by default
ALPACA_DATA_URL = os.getenv('ALPACA_DATA_URL', 'https://data.alpaca.markets')
ALPACA_MIN_ORDER_SIZE = float(os.getenv('ALPACA_MIN_ORDER_SIZE', 1))  # Minimum order size in units
ALPACA_MAX_POSITIONS = int(os.getenv('ALPACA_MAX_POSITIONS', MAX_OPEN_POSITIONS))  # Maximum number of open positions

# Helper functions
def is_forex_pair(symbol):
    """Check if a symbol is a forex pair"""
    return '/' in symbol

def get_instrument_type(symbol):
    """Get the instrument type based on the symbol"""
    if '/' in symbol:
        # Special cases
        if symbol.startswith('XAU/') or symbol.startswith('XAG/'):
            return 'commodity'
        return 'forex'
    return 'stock'