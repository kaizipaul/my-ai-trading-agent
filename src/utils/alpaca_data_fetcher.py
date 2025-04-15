"""
Alpaca Markets data fetcher for retrieving market data
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from termcolor import cprint
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# Load environment variables
load_dotenv()

class AlpacaDataFetcher:
    def __init__(self):
        """Initialize the Alpaca data fetcher"""
        # Get API credentials from environment variables
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.api_secret = os.getenv("ALPACA_API_SECRET")
        self.base_url = os.getenv("ALPACA_API_URL", "https://paper-api.alpaca.markets")
        self.data_url = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")
        
        # Check if credentials are provided
        if not self.api_key or not self.api_secret:
            cprint("⚠️ Alpaca API credentials not found in environment variables", "yellow")
            cprint("🔑 Please set ALPACA_API_KEY and ALPACA_API_SECRET in .env file", "yellow")
            self.is_configured = False
        else:
            self.is_configured = True
            
            # Initialize Alpaca API
            try:
                self.api = tradeapi.REST(
                    self.api_key,
                    self.api_secret,
                    self.base_url,
                    api_version='v2'
                )
                cprint(f"✅ Connected to Alpaca Data API", "green")
            except Exception as e:
                cprint(f"❌ Failed to connect to Alpaca API: {str(e)}", "red")
                self.is_configured = False
    
    def get_price_data(self, symbol, timeframe='1h', count=100):
        """
        Get historical price data from Alpaca
        
        Args:
            symbol (str): The trading pair or stock symbol
            timeframe (str): Timeframe for the data (e.g., '1m', '5m', '1h', '1d')
            count (int): Number of bars to fetch
            
        Returns:
            pandas.DataFrame: Dataframe with OHLCV data and date index
        """
        if not self.is_configured:
            cprint(f"⚠️ Alpaca API not configured, cannot fetch data", "yellow")
            return None
            
        try:
            # Convert forex symbols if needed (e.g., EUR/USD to EUR-USD)
            if '/' in symbol:
                alpaca_symbol = symbol.replace('/', '-')
            else:
                alpaca_symbol = symbol
                
            # Map timeframe to Alpaca format
            timeframe_map = {
                '1m': '1Min',
                '5m': '5Min',
                '15m': '15Min',
                '30m': '30Min',
                '1h': '1Hour',
                '4h': '4Hour',
                '1d': '1Day',
                '1D': '1Day',
                '1w': '1Week'
            }
            
            alpaca_timeframe = timeframe_map.get(timeframe, '1Day')
            
            # Calculate start and end dates
            end_time = datetime.now()
            
            # For higher timeframes, we need to go further back to get enough data
            if timeframe in ['1d', '1D']:
                start_time = end_time - timedelta(days=count * 1.5)
            elif timeframe in ['1h', '4h']:
                start_time = end_time - timedelta(days=count * 0.2)
            else:
                start_time = end_time - timedelta(days=10)  # Default for lower timeframes
            
            # Get the data
            bars = self.api.get_bars(
                alpaca_symbol, 
                alpaca_timeframe,
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                limit=count
            ).df
            
            if len(bars) > 0:
                # Rename columns to match our system's expected format
                bars = bars.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                
                # Make sure we have the right number of rows
                if len(bars) > count:
                    bars = bars.iloc[-count:]
                
                cprint(f"✅ Fetched {len(bars)} bars of {timeframe} data for {symbol}", "green")
                return bars
            else:
                cprint(f"⚠️ No data found for {symbol} with timeframe {timeframe}", "yellow")
                return None
                
        except Exception as e:
            cprint(f"❌ Error getting market data for {symbol}: {str(e)}", "red")
            return None
    
    def get_current_price(self, symbol):
        """Get the current market price for a symbol"""
        if not self.is_configured:
            cprint(f"⚠️ Alpaca API not configured, cannot fetch price", "yellow")
            return None
            
        try:
            # Convert forex symbols if needed
            if '/' in symbol:
                alpaca_symbol = symbol.replace('/', '-')
            else:
                alpaca_symbol = symbol
                
            # Get last quote
            quote = self.api.get_latest_quote(alpaca_symbol)
            
            # Calculate mid price
            price = (float(quote.bidprice) + float(quote.askprice)) / 2
            
            return price
        except Exception as e:
            cprint(f"❌ Error getting current price for {symbol}: {str(e)}", "red")
            return None
    
    def get_symbols(self, asset_class=None):
        """Get available trading symbols from Alpaca"""
        if not self.is_configured:
            cprint(f"⚠️ Alpaca API not configured, cannot fetch symbols", "yellow")
            return []
            
        try:
            assets = self.api.list_assets(status='active')
            
            if asset_class:
                assets = [a for a in assets if a.class_name == asset_class]
                
            return [a.symbol for a in assets]
        except Exception as e:
            cprint(f"❌ Error getting symbols: {str(e)}", "red")
            return [] 