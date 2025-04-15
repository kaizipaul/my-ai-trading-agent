"""
Utility for fetching forex market data
"""
import os
import pandas as pd
from datetime import datetime, timedelta
from termcolor import cprint
from src.utils.forex_dot_com_client import ForexDotComClient

class ForexDataFetcher:
    def __init__(self):
        """Initialize the data fetcher with FOREX.com client"""
        self.client = ForexDotComClient()
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    def get_price_data(self, pair, timeframe='H1', count=100):
        """Fetch historical price data for a forex pair"""
        try:
            # In development mode, return simulated data if no client is available
            if self.environment == "development":
                return self._get_simulated_data(pair, timeframe, count)
                
            # Format pair for FOREX.com (e.g., "EUR_USD" instead of "EUR/USD")
            formatted_pair = self.client.format_symbol(pair)
            
            # Get data from FOREX.com API
            response = self.client.get_price_data(formatted_pair, timeframe, count)
            
            if not response or 'candles' not in response:
                cprint(f"❌ No data returned for {pair}", "red")
                return None
                
            # Convert to pandas DataFrame
            data = []
            for candle in response['candles']:
                if candle.get('complete', True):  # Assume candle is complete if not specified
                    data.append({
                        'timestamp': candle['time'],
                        'open': float(candle['mid']['o']),
                        'high': float(candle['mid']['h']),
                        'low': float(candle['mid']['l']),
                        'close': float(candle['mid']['c']),
                        'volume': candle.get('volume', 0)  # Default to 0 if volume not provided
                    })
                    
            if not data:
                cprint(f"❌ No complete candles found for {pair}", "red")
                return None
                
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            cprint(f"❌ Error fetching price data: {str(e)}", "red")
            return self._get_simulated_data(pair, timeframe, count) if self.environment == "development" else None
            
    def get_current_price(self, pair):
        """Get current market price for a pair"""
        try:
            # In development mode, return simulated data if no client is available
            if self.environment == "development":
                return self._get_simulated_current_price(pair)
                
            # Format pair for FOREX.com
            formatted_pair = self.client.format_symbol(pair)
            
            # Get current price from FOREX.com API
            price = self.client.get_current_price(formatted_pair)
            
            if price is None:
                cprint(f"❌ Failed to get current price for {pair}", "red")
                return self._get_simulated_current_price(pair) if self.environment == "development" else None
                
            return float(price)
            
        except Exception as e:
            cprint(f"❌ Error fetching current price: {str(e)}", "red")
            return self._get_simulated_current_price(pair) if self.environment == "development" else None
            
    def _get_simulated_data(self, pair, timeframe, count):
        """Generate simulated price data for development mode"""
        cprint(f"🔵 [SIMULATION] Generating simulated data for {pair}", "blue")
        
        # Create date range
        end_date = datetime.now()
        
        # Determine time delta based on timeframe
        if timeframe == 'M1' or timeframe == '1m':
            delta = timedelta(minutes=1)
        elif timeframe == 'M5' or timeframe == '5m':
            delta = timedelta(minutes=5)
        elif timeframe == 'M15' or timeframe == '15m':
            delta = timedelta(minutes=15)
        elif timeframe == 'H1' or timeframe == '1h':
            delta = timedelta(hours=1)
        elif timeframe == 'H4' or timeframe == '4h':
            delta = timedelta(hours=4)
        elif timeframe == 'D' or timeframe == '1d':
            delta = timedelta(days=1)
        else:
            delta = timedelta(hours=1)  # Default to 1 hour
            
        # Create date range
        dates = [end_date - delta * i for i in range(count)]
        dates.reverse()
        
        # Generate random price data
        # Base values for major pairs
        base_prices = {
            'EUR/USD': 1.1000,
            'GBP/USD': 1.3000,
            'USD/JPY': 115.00,
            'XAU/USD': 1800.00
        }
        
        # Use a reasonable base price or default to 1.0
        base_price = base_prices.get(pair, 1.0)
        volatility = base_price * 0.002  # 0.2% volatility
        
        # Generate OHLC data
        import numpy as np
        np.random.seed(42)  # For reproducibility
        
        closes = base_price + np.random.normal(0, volatility, count).cumsum()
        data = []
        
        for i, date in enumerate(dates):
            close = closes[i]
            high = close + abs(np.random.normal(0, volatility))
            low = close - abs(np.random.normal(0, volatility))
            open_price = closes[i-1] if i > 0 else close + np.random.normal(0, volatility)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': int(np.random.random() * 1000)
            })
            
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
        
    def _get_simulated_current_price(self, pair):
        """Generate a simulated current price for development mode"""
        # Base values for major pairs
        base_prices = {
            'EUR/USD': 1.1000,
            'GBP/USD': 1.3000,
            'USD/JPY': 115.00,
            'XAU/USD': 1800.00
        }
        
        # Get base price or use default
        base_price = base_prices.get(pair, 1.0)
        
        # Add small random variation
        import random
        variation = random.uniform(-0.001, 0.001)
        
        current_price = base_price + (base_price * variation)
        return current_price