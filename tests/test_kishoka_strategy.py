"""
Test script for the Kishoka Killswitch strategy
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from termcolor import cprint

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.yfinance_data_fetcher import YFinanceDataFetcher
from src.utils.technical_analysis import TechnicalAnalysis
from src.strategies.kishoka_strategy import KishokaStrategy

def generate_test_data():
    """Generate synthetic price data with clear swing points for testing"""
    # Create date range for the last 100 days
    end_date = datetime.now()
    date_range = pd.date_range(end=end_date, periods=100, freq='D')
    
    # Create a price series with clear swings (a sine wave pattern)
    base_price = 100.0
    amplitude = 10.0
    x = np.linspace(0, 6*np.pi, 100)  # Multiple complete cycles
    closes = base_price + amplitude * np.sin(x)
    
    # Add some noise to make it more realistic
    noise = np.random.normal(0, 0.5, 100)
    closes = closes + noise
    
    # Create OHLC data
    data = []
    for i, date in enumerate(date_range):
        close = closes[i]
        # Make highs and lows more extreme at swing points
        high_factor = 1.0 + 0.01 * abs(np.sin(x[i]))
        low_factor = 1.0 - 0.01 * abs(np.sin(x[i]))
        
        high = close * high_factor
        low = close * low_factor
        
        # Open price is close to previous close
        open_price = closes[i-1] if i > 0 else close * 0.99
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(1000, 10000)
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    return df

def test_kishoka_strategy():
    """Test the Kishoka Killswitch strategy with synthetic data"""
    cprint("\n" + "="*60, "blue")
    cprint("TESTING KISHOKA KILLSWITCH STRATEGY", "blue")
    cprint("="*60 + "\n", "blue")
    
    # Create strategy instance
    strategy = KishokaStrategy()
    
    # Generate test data
    cprint("Generating test data with clear swing patterns...", "cyan")
    df = generate_test_data()
    
    # Add technical indicators
    df = TechnicalAnalysis.add_all_indicators(df)
    
    # Apply strategy to test data
    cprint("Applying Kishoka strategy...", "cyan")
    result = strategy._apply_kishoka_strategy(df, pip_size=0.01)
    
    # Count signals
    long_entries = len(result[(result['position'] == 1) & (result['position'].shift(1) == 0)])
    short_entries = len(result[(result['position'] == -1) & (result['position'].shift(1) == 0)])
    position_moves = len(result[result['position'] != result['position'].shift(1)])
    
    # Display summary statistics
    cprint("\nStrategy Results:", "green")
    cprint(f"Data points analyzed: {len(df)}", "white")
    cprint(f"Long entries: {long_entries}", "green")
    cprint(f"Short entries: {short_entries}", "red")
    cprint(f"Total position changes: {position_moves}", "yellow")
    
    # Generate signals using the generate_signal method
    cprint("\nTesting generate_signal method...", "cyan")
    
    # Test with different symbols
    test_symbols = ['EUR/USD', 'AAPL']
    
    for symbol in test_symbols:
        signal = strategy.generate_signal(symbol, df)
        
        if signal:
            cprint(f"\nSignal for {symbol}:", "green")
            cprint(f"Direction: {signal['direction']}", "white")
            cprint(f"Confidence: {signal['confidence']:.2f}", "white")
            cprint(f"Entry price: {signal['entry_price']:.4f}", "white")
            cprint(f"Stop loss: {signal['stop_loss']:.4f}", "white")
            cprint(f"Take profit: {signal['take_profit']:.4f}", "white")
            
            # Display risk/reward
            risk = abs(signal['entry_price'] - signal['stop_loss'])
            reward = abs(signal['entry_price'] - signal['take_profit'])
            ratio = reward / risk if risk > 0 else 0
            cprint(f"Risk/Reward ratio: 1:{ratio:.2f}", "white")
        else:
            cprint(f"No signal generated for {symbol}", "yellow")
    
    cprint("\nTest completed!", "green")

def test_with_real_data():
    """Test the Kishoka strategy with real market data"""
    cprint("\n" + "="*60, "magenta")
    cprint("TESTING KISHOKA STRATEGY WITH MARKET DATA", "magenta")
    cprint("="*60 + "\n", "magenta")
    
    # Force development mode for reliable testing
    os.environ["ENVIRONMENT"] = "development"
    
    # Initialize components
    data_fetcher = YFinanceDataFetcher()
    strategy = KishokaStrategy()
    
    # Test with different symbols
    symbols = ['EUR/USD', 'AAPL', 'XAU/USD']
    
    for symbol in symbols:
        cprint(f"\nTesting {symbol}...", "cyan")
        
        # Fetch market data
        df = data_fetcher.get_price_data(symbol, timeframe='1d', count=200)
        
        if df is not None:
            # Add technical indicators
            df = TechnicalAnalysis.add_all_indicators(df)
            
            # Apply strategy
            result = strategy._apply_kishoka_strategy(df, pip_size=strategy._get_pip_size(symbol))
            
            # Count signals
            long_entries = len(result[(result['position'] == 1) & (result['position'].shift(1) == 0)])
            short_entries = len(result[(result['position'] == -1) & (result['position'].shift(1) == 0)])
            
            cprint(f"Results for {symbol}:", "green")
            cprint(f"Data points: {len(df)}", "white")
            cprint(f"Long entries: {long_entries}", "green")
            cprint(f"Short entries: {short_entries}", "red")
            
            # Get the latest signal
            signal = strategy.generate_signal(symbol, df)
            
            if signal:
                cprint(f"\nLatest signal for {symbol}:", "yellow")
                cprint(f"Direction: {signal['direction'].upper()}", "white")
                cprint(f"Entry price: {signal['entry_price']:.4f}", "white")
                cprint(f"Stop loss: {signal['stop_loss']:.4f}", "white")
                cprint(f"Take profit: {signal['take_profit']:.4f}", "white")
            else:
                cprint("No active signal at the moment", "yellow")
        else:
            cprint(f"Failed to get data for {symbol}", "red")
    
    cprint("\nMarket data test completed!", "green")

if __name__ == "__main__":
    # Run synthetic data test
    test_kishoka_strategy()
    
    # Run real market data test
    test_with_real_data() 