"""
Technical analysis agent for forex markets
"""
import pandas as pd
from termcolor import cprint

# Try to import pandas_ta, but provide fallback if it fails
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    cprint("Warning: pandas_ta module not available, using fallback implementation", "yellow")

from src.config import FOREX_PAIRS, TIMEFRAMES, RSI_PERIOD
from src.utils.forex_data_fetcher import ForexDataFetcher
from src.utils.technical_analysis import TechnicalAnalysis

class TechnicalAgent:
    def __init__(self):
        self.data_fetcher = ForexDataFetcher()
        
    def analyze_pair(self, pair):
        """Analyze a forex pair using technical indicators"""
        try:
            # Get market data
            data = self.data_fetcher.get_price_data(pair)
            if data is None or len(data) < 200:  # Need enough data for 200 MA
                return None
                
            # Use the TechnicalAnalysis utility to add indicators
            data = TechnicalAnalysis.add_all_indicators(data)
            
            # Generate trading signals
            trading_signal = self.generate_trading_signal(data)
            
            cprint(f"📊 Technical Analysis for {pair}: {trading_signal}", "cyan")
            return trading_signal
            
        except Exception as e:
            cprint(f"❌ Error analyzing {pair}: {str(e)}", "red")
            return None
                
    def generate_trading_signal(self, data):
        """Generate trading signal based on technical indicators"""
        # This is a simple example - you should expand this based on your strategy
        signal = {
            'should_trade': False,
            'direction': None,
            'strength': 0
        }
        
        # Check if RSI indicates oversold/overbought
        if 'rsi' in data.columns:
            last_rsi = data['rsi'].iloc[-1]
            if last_rsi < 30:
                signal['should_trade'] = True
                signal['direction'] = 'buy'
                signal['strength'] = 0.7
            elif last_rsi > 70:
                signal['should_trade'] = True
                signal['direction'] = 'sell'
                signal['strength'] = 0.7
        
        # Add more conditions based on other indicators
        
        return signal