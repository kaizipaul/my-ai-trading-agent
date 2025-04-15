"""
Test script for the trading agent with Kishoka Killswitch strategy
"""
import os
import sys
from termcolor import cprint

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.agents.trading_agent import ForexTradingAgent
from src.strategies.kishoka_strategy import KishokaStrategy

def test_trading_agent_with_kishoka():
    """Test the trading agent with the Kishoka strategy"""
    # Force development mode for reliable testing
    os.environ["ENVIRONMENT"] = "development"
    
    cprint("\n" + "="*60, "green")
    cprint("TESTING TRADING AGENT WITH KISHOKA STRATEGY", "green")
    cprint("="*60 + "\n", "green")
    
    # Initialize the trading agent
    trading_agent = ForexTradingAgent()
    
    # Verify the Kishoka strategy is registered
    if 'kishoka_killswitch' in trading_agent.strategies:
        cprint("✅ Kishoka strategy is registered in the trading agent", "green")
    else:
        cprint("❌ Kishoka strategy is NOT registered", "red")
        return
    
    # Test with a single symbol
    test_symbol = 'EUR/USD'
    cprint(f"\nAnalyzing {test_symbol} with all registered strategies...", "cyan")
    
    # Analyze the pair
    trading_agent.analyze_pair(test_symbol)
    
    # Check if we got any recommendations
    if test_symbol in trading_agent.recommendations:
        recommendation = trading_agent.recommendations[test_symbol]
        cprint("\nRecommendation received:", "green")
        cprint(f"Strategy: {recommendation['strategy']}", "white")
        cprint(f"Direction: {recommendation['recommendation']}", "white")
        cprint(f"Confidence: {recommendation['confidence']:.2f}", "white")
        cprint(f"Entry Price: {recommendation['entry_price']}", "white")
        cprint(f"Stop Loss: {recommendation['stop_loss']}", "white")
        cprint(f"Take Profit: {recommendation['take_profit']}", "white")
        
        # Check if the recommendation came from the Kishoka strategy
        if recommendation['strategy'] == 'kishoka_killswitch':
            cprint("✅ Recommendation is from Kishoka strategy", "green")
        else:
            cprint(f"Recommendation is from {recommendation['strategy']} strategy", "yellow")
    else:
        cprint("No recommendation generated for the symbol", "yellow")
    
    cprint("\nTest completed!", "green")

if __name__ == "__main__":
    test_trading_agent_with_kishoka() 