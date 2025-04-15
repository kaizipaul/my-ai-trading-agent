"""
Test script for the Position Recommender
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.yfinance_data_fetcher import YFinanceDataFetcher
from src.utils.position_recommender import PositionRecommender
from src.utils.technical_analysis import TechnicalAnalysis

def generate_test_data(symbol, days=100):
    """Generate test data for the position recommender"""
    # If we have a real fetcher, try to use it first
    fetcher = YFinanceDataFetcher()
    df = fetcher.get_price_data(symbol, timeframe='1d', count=days)
    
    # If we got real data, use it
    if df is not None and not df.empty and len(df) >= 20:
        print(f"Using real data for {symbol}")
        return TechnicalAnalysis.add_all_indicators(df)
    
    # Otherwise, generate simulated data
    print(f"Generating simulated data for {symbol}")
    
    # Set base prices for different symbols
    base_prices = {
        'AAPL': 180.0,
        'MSFT': 380.0,
        'GOOG': 140.0,
        'EUR/USD': 1.09,
        'GBP/USD': 1.25,
        'USD/JPY': 150.0,
        'XAU/USD': 2000.0,
    }
    
    # Set price and volatility based on symbol
    base_price = base_prices.get(symbol, 100.0)
    volatility = base_price * 0.01  # 1% volatility
    
    # Create date range
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='D')
    
    # Generate price data
    np.random.seed(42)  # For reproducibility
    
    # Generate a trending price series
    trend = np.linspace(-0.1, 0.1, days)  # -10% to +10% trend
    noise = np.random.normal(0, volatility, days)
    closes = base_price * (1 + trend + noise.cumsum() * 0.01)
    
    # Generate OHLCV data
    data = []
    for i, date in enumerate(dates):
        close = closes[i]
        high = close * (1 + abs(np.random.normal(0, 0.005)))
        low = close * (1 - abs(np.random.normal(0, 0.005)))
        open_price = closes[i-1] if i > 0 else close * (1 + np.random.normal(0, 0.005))
        volume = int(np.random.random() * 10000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
        })
    
    # Create DataFrame
    df = pd.DataFrame(data, index=dates)
    
    # Add technical indicators
    df = TechnicalAnalysis.add_all_indicators(df)
    
    return df

def test_recommender():
    """Test the Position Recommender with simulated data"""
    recommender = PositionRecommender()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'EUR/USD', 'XAU/USD']
    
    print("\n===== Testing Position Recommender =====")
    
    for symbol in test_symbols:
        print(f"\n----- Testing {symbol} -----")
        
        # Generate test data with a strong trend
        df = generate_test_data(symbol)
        
        # Get recommendation
        recommendation = recommender.analyze_and_recommend(symbol, df)
        
        # Display recommendation
        output_lines, color = recommender.format_recommendation_output(recommendation)
        for line in output_lines:
            print(line)
            
        # Add extra newline
        print()
    
    print("\n===== All tests completed =====")

def test_different_signal_patterns():
    """Test the Position Recommender with different signal patterns"""
    recommender = PositionRecommender()
    symbol = "TEST"
    
    print("\n===== Testing Different Signal Patterns =====")
    
    # Test 1: Strongly Bullish
    print("\n----- Testing Strongly Bullish Pattern -----")
    df = generate_test_data(symbol)
    
    # Force bullish signals
    df['rsi'] = 60  # Moderately high RSI but not overbought
    df['macd'] = 2  # MACD above zero
    df['macd_signal'] = 1  # MACD above signal line
    df['sma_50'] = df['close'] * 0.9  # Price well above MA
    
    recommendation = recommender.analyze_and_recommend(symbol, df)
    output_lines, _ = recommender.format_recommendation_output(recommendation)
    for line in output_lines:
        print(line)
    
    # Test 2: Strongly Bearish
    print("\n----- Testing Strongly Bearish Pattern -----")
    df = generate_test_data(symbol)
    
    # Force bearish signals
    df['rsi'] = 30  # Low RSI
    df['macd'] = -2  # MACD below zero
    df['macd_signal'] = -1  # MACD below signal line
    df['sma_50'] = df['close'] * 1.1  # Price below MA
    
    recommendation = recommender.analyze_and_recommend(symbol, df)
    output_lines, _ = recommender.format_recommendation_output(recommendation)
    for line in output_lines:
        print(line)
    
    # Test 3: Neutral/Conflicting
    print("\n----- Testing Neutral Pattern -----")
    df = generate_test_data(symbol)
    
    # Force neutral signals
    df['rsi'] = 50  # Neutral RSI
    df['macd'] = 0.1  # MACD barely above zero
    df['macd_signal'] = 0.2  # MACD below signal line
    df['sma_50'] = df['close']  # Price at MA
    
    recommendation = recommender.analyze_and_recommend(symbol, df)
    output_lines, _ = recommender.format_recommendation_output(recommendation)
    for line in output_lines:
        print(line)
    
    print("\n===== All pattern tests completed =====")

if __name__ == "__main__":
    # Force development mode for testing
    os.environ["ENVIRONMENT"] = "development"
    
    # Run the basic recommender test
    test_recommender()
    
    # Run the pattern tests
    test_different_signal_patterns() 