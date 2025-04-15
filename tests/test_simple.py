"""
Simple test script for the Yahoo Finance data fetcher and Position Recommender
"""
import os
import sys
import time
from termcolor import cprint

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.yfinance_data_fetcher import YFinanceDataFetcher
from src.utils.position_recommender import PositionRecommender
from src.utils.technical_analysis import TechnicalAnalysis

def test_simple_recommendation():
    """Test the position recommender with a few symbols"""
    # Force development mode for reliable testing
    os.environ["ENVIRONMENT"] = "development"
    
    # Initialize components
    data_fetcher = YFinanceDataFetcher()
    recommender = PositionRecommender()
    
    # Test with a few popular symbols - organized by type for better testing
    symbol_groups = [
        # Stocks
        ['AAPL', 'MSFT'],
        # Forex
        ['EUR/USD', 'GBP/USD'],
        # Commodities
        ['XAU/USD', 'XAG/USD']
    ]
    
    # Process each group with delay between groups to avoid rate limiting
    for i, symbols in enumerate(symbol_groups):
        if i > 0:
            # Add delay between groups to avoid rate limits
            cprint(f"\n⏳ Waiting a few seconds before next symbol group to avoid rate limits...", "yellow")
            time.sleep(5)  # 5 second delay between groups
    
        cprint(f"\n{'='*50}", "blue")
        cprint(f"Symbol Group {i+1}: {', '.join(symbols)}", "blue")
        cprint(f"{'='*50}", "blue")
        
        for symbol in symbols:
            cprint(f"\n{'-'*40}", "cyan")
            cprint(f"Analyzing {symbol}...", "cyan")
            cprint(f"{'-'*40}", "cyan")
            
            # Get price data - try different timeframes if one fails
            timeframes = ['1d', '1h', '5m']
            data = None
            
            for tf in timeframes:
                try:
                    cprint(f"Attempting to fetch {symbol} with {tf} timeframe...", "blue")
                    data = data_fetcher.get_price_data(symbol, timeframe=tf, count=100)
                    if data is not None and not data.empty:
                        cprint(f"✅ Successfully retrieved {len(data)} periods of {tf} data for {symbol}", "green")
                        break
                except Exception as e:
                    cprint(f"⚠️ Error with {tf} timeframe: {str(e)}", "yellow")
                    time.sleep(1)  # Short delay before trying next timeframe
            
            if data is not None and not data.empty:
                # Add technical indicators
                data = TechnicalAnalysis.add_all_indicators(data)
                
                # Generate recommendation
                recommendation = recommender.analyze_and_recommend(symbol, data)
                
                # Display recommendation
                output_lines, color = recommender.format_recommendation_output(recommendation)
                for line in output_lines:
                    cprint(line, color)
            else:
                cprint(f"❌ Failed to get data for {symbol} after trying multiple timeframes", "red")
                
            # Add a small delay between symbols in the same group
            if symbol != symbols[-1]:
                time.sleep(2)
                
        cprint("\n")
        
def test_cached_data():
    """Test that data caching is working properly"""
    cprint("\n" + "="*60, "magenta")
    cprint("TESTING DATA CACHE FUNCTIONALITY", "magenta")
    cprint("="*60 + "\n", "magenta")
    
    # Force development mode for reliable testing
    os.environ["ENVIRONMENT"] = "development"
    
    # Initialize data fetcher
    data_fetcher = YFinanceDataFetcher()
    
    # Pick one symbol for testing
    symbol = 'AAPL'
    timeframe = '1d'
    count = 100
    
    # Create a unique cache key based on current timestamp
    # This ensures we're testing fresh cache creation and retrieval
    unique_symbol = f"{symbol}_{int(time.time())}"
    cprint(f"Using unique symbol {unique_symbol} to ensure fresh cache testing", "cyan")
    
    # First fetch - should generate simulated data and cache it
    cprint(f"First request (should create new simulated data):", "cyan")
    start_time = time.time()
    data1 = data_fetcher._get_simulated_data(unique_symbol, timeframe, count)
    # Manually save to cache
    data_fetcher._save_to_cache(unique_symbol, timeframe, count, data1)
    fetch_time1 = time.time() - start_time
    
    if data1 is not None:
        cprint(f"✅ Generated simulated data and saved to cache", "green")
        # Wait a moment to make timing more accurate
        time.sleep(1)
        
        # Second fetch - should come from cache
        cprint(f"\nSecond request (should use cache):", "cyan")
        start_time = time.time()
        data2 = data_fetcher.get_price_data(unique_symbol, timeframe=timeframe, count=count)
        fetch_time2 = time.time() - start_time
        
        # Compare results
        if data2 is not None:
            # Check if data matches
            data_match = data1.equals(data2)
            
            cprint(f"\nResults:", "green")
            cprint(f"- First fetch took: {fetch_time1:.2f} seconds", "white")
            cprint(f"- Second fetch took: {fetch_time2:.2f} seconds", "white")
            cprint(f"- Speed improvement: {fetch_time1/fetch_time2:.1f}x faster", "green" if fetch_time2 < fetch_time1 else "yellow")
            cprint(f"- Data shapes match: {data1.shape == data2.shape}", "green" if data1.shape == data2.shape else "red")
            cprint(f"- Data content matches: {data_match}", "green" if data_match else "red")
        else:
            cprint(f"❌ Failed to get cached data on second attempt", "red")
    else:
        cprint(f"❌ Failed to generate simulated data on first attempt", "red")
    
if __name__ == "__main__":
    cprint("\n" + "="*60, "green")
    cprint("TESTING POSITION RECOMMENDATION SYSTEM", "green")
    cprint("="*60 + "\n", "green")
    
    test_simple_recommendation()
    
    # Also test the cache functionality
    test_cached_data() 