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


class ConfigError(Exception):
    """Raised when the system's configuration is invalid or unsafe to start with"""
    pass


def validate_config():
    """
    Validate configuration at startup.

    Raises ConfigError with a clear, actionable message instead of letting
    the system start in a broken or unexpectedly unsafe state - e.g.
    EXECUTE_TRADES=true with no way to actually reach Alpaca, or a live
    (real-money) endpoint enabled without an explicit opt-in.
    """
    errors = []

    if not FOREX_PAIRS:
        errors.append("SYMBOLS must include at least one trading symbol")

    if not (0 < MAX_POSITION_SIZE <= 1):
        errors.append(f"MAX_RISK_PER_TRADE must be between 0 and 1 (got {MAX_POSITION_SIZE})")

    if not (0 < MAX_DAILY_LOSS <= 1):
        errors.append(f"MAX_DAILY_LOSS must be between 0 and 1 (got {MAX_DAILY_LOSS})")

    if MAX_OPEN_POSITIONS <= 0:
        errors.append(f"MAX_OPEN_POSITIONS must be positive (got {MAX_OPEN_POSITIONS})")

    if EXECUTE_TRADES:
        if not ALPACA_API_KEY or not ALPACA_API_SECRET:
            errors.append(
                "EXECUTE_TRADES=true requires ALPACA_API_KEY and ALPACA_API_SECRET to be set - "
                "refusing to start with trade execution enabled but no way to reach Alpaca"
            )

        is_live_endpoint = 'paper-api' not in ALPACA_API_URL
        allow_live = os.getenv('ALLOW_LIVE_TRADING', 'false').lower() in ('true', '1', 't')
        if is_live_endpoint and not allow_live:
            errors.append(
                f"ALPACA_API_URL ({ALPACA_API_URL}) points to a LIVE trading endpoint, not "
                "paper-api.alpaca.markets. Set ALLOW_LIVE_TRADING=true in your .env if this is "
                "intentional - this check exists to stop accidental real-money trading."
            )

    if errors:
        raise ConfigError("Invalid configuration:\n  - " + "\n  - ".join(errors))