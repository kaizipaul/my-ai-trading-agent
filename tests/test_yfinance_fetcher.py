"""
Test script for the Yahoo Finance data fetcher
"""
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.yfinance_data_fetcher import YFinanceDataFetcher

def test_fetcher():
    """Test the Yahoo Finance data fetcher with various symbols"""
    fetcher = YFinanceDataFetcher()
    
    # Test with different instrument types
    test_symbols = [
        'AAPL',         # Stock
        'EUR/USD',      # Forex
        'XAU/USD',      # Gold (commodity)
        'BTC-USD',      # Crypto
    ]
    
    print("\n===== Testing Yahoo Finance Data Fetcher =====")
    
    for symbol in test_symbols:
        print(f"\n----- Testing {symbol} -----")
        
        # Test daily data
        print(f"Fetching daily data for {symbol}...")
        df_daily = fetcher.get_price_data(symbol, timeframe='1d', count=5)
        if df_daily is not None:
            print(f"✅ Got {len(df_daily)} daily candles")
            print(df_daily.head())
        else:
            print(f"❌ Failed to get daily data for {symbol}")
        
        # Test hourly data
        print(f"\nFetching hourly data for {symbol}...")
        df_hourly = fetcher.get_price_data(symbol, timeframe='1h', count=5)
        if df_hourly is not None:
            print(f"✅ Got {len(df_hourly)} hourly candles")
            print(df_hourly.head())
        else:
            print(f"❌ Failed to get hourly data for {symbol}")
        
        # Test current price
        print(f"\nFetching current price for {symbol}...")
        current_price = fetcher.get_current_price(symbol)
        if current_price is not None:
            print(f"✅ Current price: {current_price}")
        else:
            print(f"❌ Failed to get current price for {symbol}")
    
    print("\n===== All tests completed =====")

if __name__ == "__main__":
    # Force development mode for testing
    os.environ["ENVIRONMENT"] = "development"
    test_fetcher() 