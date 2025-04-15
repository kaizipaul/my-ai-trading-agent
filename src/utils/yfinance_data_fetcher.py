"""
Utility for fetching financial market data using Yahoo Finance
"""
import os
import pandas as pd
import yfinance as yf
import numpy as np
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from termcolor import cprint

class YFinanceDataFetcher:
    def __init__(self):
        """Initialize the data fetcher with Yahoo Finance"""
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.cache_dir = self._setup_cache_directory()
        self.cache_duration = 1  # Cache duration in hours
        self.max_retries = 3
        self.base_delay = 2  # Base delay in seconds for retry
        
    def _setup_cache_directory(self):
        """Set up cache directory for storing fetched data"""
        # Create a cache directory in the data folder
        cache_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "cache"
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
        
    def get_price_data(self, symbol, timeframe='1h', count=100):
        """Fetch historical price data for a financial instrument
        
        Args:
            symbol (str): The ticker symbol (e.g., 'EURUSD=X' for EUR/USD)
            timeframe (str): The timeframe ('1h', '1d', etc.)
            count (int): Number of candles to fetch
        
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        # Check cache first
        cached_data = self._get_from_cache(symbol, timeframe, count)
        if cached_data is not None:
            return cached_data
            
        # If data not in cache, fetch from Yahoo Finance
        try:
            # Convert forex pair to Yahoo Finance format if needed
            yf_symbol = self._convert_to_yf_symbol(symbol)
            
            # Calculate start and end dates based on timeframe and count
            end_date = datetime.now()
            
            # Determine the period based on timeframe and count
            if timeframe == '1m':
                period = timedelta(minutes=count)
                interval = "1m"
            elif timeframe == '5m':
                period = timedelta(minutes=5 * count)
                interval = "5m"
            elif timeframe == '15m':
                period = timedelta(minutes=15 * count)
                interval = "15m"
            elif timeframe == '30m':
                period = timedelta(minutes=30 * count)
                interval = "30m"
            elif timeframe == '1h':
                period = timedelta(hours=count)
                interval = "1h"
            elif timeframe == '1d':
                period = timedelta(days=count)
                interval = "1d"
            else:
                # Default to 1d
                period = timedelta(days=count)
                interval = "1d"
                
            start_date = end_date - period
            
            # Adjust for weekends and fetch more data than needed
            if interval in ['1d', '1wk', '1mo']:
                start_date = start_date - timedelta(days=count//3)
            
            # Fetch data from Yahoo Finance with retry logic
            df = self._fetch_with_retry(yf_symbol, start_date, end_date, interval)
            
            # If we got no data, try with a longer timeframe
            if df is None or len(df) == 0:
                cprint(f"⚠️ No data found for {yf_symbol} with interval {interval}. Trying with daily data.", "yellow")
                # Add a delay to avoid rate limiting
                time.sleep(1)
                df = self._fetch_with_retry(
                    yf_symbol,
                    start_date - timedelta(days=30),  # Go further back
                    end_date,
                    "1d"  # Use daily data
                )
            
            # Check if we have any data
            if df is None or len(df) == 0:
                cprint(f"❌ No data available for {yf_symbol}", "red")
                if self.environment == "development":
                    df = self._get_simulated_data(symbol, timeframe, count)
                    # Save simulated data to cache
                    self._save_to_cache(symbol, timeframe, count, df)
                    return df
                return None
            
            # Process the data
            df = self._process_data_frame(df, count)
            
            # Save to cache
            self._save_to_cache(symbol, timeframe, count, df)
            
            return df
            
        except Exception as e:
            cprint(f"❌ Error fetching price data: {str(e)}", "red")
            if self.environment == "development":
                df = self._get_simulated_data(symbol, timeframe, count)
                # Save simulated data to cache
                self._save_to_cache(symbol, timeframe, count, df)
                return df
            return None
    
    def _fetch_with_retry(self, symbol, start_date, end_date, interval, current_retry=0):
        """Fetch data with exponential backoff retry logic"""
        try:
            # Add a small random delay to avoid consecutive rapid requests
            jitter = random.uniform(0.1, 0.5)
            time.sleep(jitter)
            
            cprint(f"📈 Fetching {symbol} data from Yahoo Finance...", "cyan")
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )
            return df
        except Exception as e:
            if "Too Many Requests" in str(e) and current_retry < self.max_retries:
                retry_delay = self.base_delay * (2 ** current_retry) + random.uniform(0, 1)
                cprint(f"⚠️ Rate limit hit. Retrying in {retry_delay:.2f} seconds (attempt {current_retry+1}/{self.max_retries})...", "yellow")
                time.sleep(retry_delay)
                return self._fetch_with_retry(symbol, start_date, end_date, interval, current_retry + 1)
            else:
                cprint(f"❌ Failed to fetch data after retries: {str(e)}", "red")
                return None
    
    def _process_data_frame(self, df, count):
        """Process the DataFrame to standardize column names and limit results"""
        if df is None or len(df) == 0:
            return None
            
        # Rename columns to match our expected format
        df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # Make sure all columns are lowercase
        df.columns = [col.lower() for col in df.columns]
        
        # If 'adj close' column exists, rename it
        if 'adj close' in df.columns:
            df.rename(columns={'adj close': 'adj_close'}, inplace=True)
        
        # Limit to the requested count
        if len(df) > count:
            df = df.iloc[-count:]
            
        return df
    
    def _get_cache_path(self, symbol, timeframe, count):
        """Get the file path for a cached data item"""
        safe_symbol = symbol.replace('/', '_').replace('\\', '_')
        filename = f"{safe_symbol}_{timeframe}_{count}.pkl"
        return self.cache_dir / filename
    
    def _get_from_cache(self, symbol, timeframe, count):
        """Try to get data from cache if available and not expired"""
        cache_path = self._get_cache_path(symbol, timeframe, count)
        
        if not cache_path.exists():
            return None
            
        # Check if cache is still valid
        cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        cache_age = datetime.now() - cache_time
        
        if cache_age > timedelta(hours=self.cache_duration):
            cprint(f"🔄 Cache expired for {symbol}, fetching fresh data...", "blue")
            return None
            
        try:
            df = pd.read_pickle(cache_path)
            cprint(f"📂 Using cached data for {symbol}", "green")
            return df
        except Exception as e:
            cprint(f"⚠️ Error reading from cache: {str(e)}", "yellow")
            return None
    
    def _save_to_cache(self, symbol, timeframe, count, df):
        """Save data to cache"""
        if df is None or len(df) == 0:
            return
            
        try:
            cache_path = self._get_cache_path(symbol, timeframe, count)
            df.to_pickle(cache_path)
            cprint(f"💾 Saved {symbol} data to cache", "green")
        except Exception as e:
            cprint(f"⚠️ Error saving to cache: {str(e)}", "yellow")
            
    def get_current_price(self, symbol):
        """Get current market price for a symbol"""
        # Check cache first with a short timeframe to get recent data
        cache_key = f"{symbol}_current_price"
        current_price_cache_path = self.cache_dir / f"{cache_key.replace('/', '_')}.json"
        
        # Check if we have a recent cached price (last 15 minutes)
        if current_price_cache_path.exists():
            cache_time = datetime.fromtimestamp(current_price_cache_path.stat().st_mtime)
            cache_age = datetime.now() - cache_time
            
            if cache_age < timedelta(minutes=15):
                try:
                    with open(current_price_cache_path, 'r') as f:
                        price_data = json.load(f)
                        cprint(f"📂 Using cached current price for {symbol}", "green")
                        return price_data['price']
                except Exception:
                    pass
        
        try:
            # Convert forex pair to Yahoo Finance format if needed
            yf_symbol = self._convert_to_yf_symbol(symbol)
            
            # Add a small random delay
            time.sleep(random.uniform(0.1, 0.3))
            
            # Get the most recent price
            ticker = yf.Ticker(yf_symbol)
            
            # Get the last quote
            try:
                last_quote = ticker.history(period="1d")
                if not last_quote.empty:
                    price = float(last_quote['Close'].iloc[-1])
                    self._save_current_price_to_cache(symbol, price)
                    return price
            except Exception:
                pass
                
            # If that fails, try to get the current market price
            try:
                market_price = ticker.info.get('regularMarketPrice')
                if market_price:
                    price = float(market_price)
                    self._save_current_price_to_cache(symbol, price)
                    return price
            except Exception:
                pass
                
            # If still no price, fallback to simulated price in development mode
            if self.environment == "development":
                price = self._get_simulated_current_price(symbol)
                self._save_current_price_to_cache(symbol, price)
                return price
                
            cprint(f"❌ Failed to get current price for {symbol}", "red")
            return None
            
        except Exception as e:
            cprint(f"❌ Error fetching current price: {str(e)}", "red")
            if self.environment == "development":
                price = self._get_simulated_current_price(symbol)
                self._save_current_price_to_cache(symbol, price)
                return price
            return None
    
    def _save_current_price_to_cache(self, symbol, price):
        """Save current price to cache"""
        try:
            cache_key = f"{symbol}_current_price"
            cache_path = self.cache_dir / f"{cache_key.replace('/', '_')}.json"
            
            with open(cache_path, 'w') as f:
                json.dump({
                    "price": price,
                    "timestamp": datetime.now().isoformat()
                }, f)
        except Exception as e:
            cprint(f"⚠️ Error saving current price to cache: {str(e)}", "yellow")
    
    def _convert_to_yf_symbol(self, symbol):
        """Convert a standard symbol format to Yahoo Finance format"""
        # Handle forex pairs (e.g., EUR/USD -> EURUSD=X)
        if '/' in symbol:
            base, quote = symbol.split('/')
            # Special case for gold
            if base == 'XAU' and quote == 'USD':
                return 'GC=F'  # Gold futures
            # Special case for silver
            elif base == 'XAG' and quote == 'USD':
                return 'SI=F'  # Silver futures
            else:
                return f"{base}{quote}=X"
        return symbol
    
    def _get_simulated_data(self, symbol, timeframe, count):
        """Generate simulated price data for development mode"""
        cprint(f"🔵 [SIMULATION] Generating simulated data for {symbol}", "blue")
        
        # Create date range
        end_date = datetime.now()
        
        # Determine time delta based on timeframe
        if timeframe == '1m':
            delta = timedelta(minutes=1)
        elif timeframe == '5m':
            delta = timedelta(minutes=5)
        elif timeframe == '15m':
            delta = timedelta(minutes=15)
        elif timeframe == '1h':
            delta = timedelta(hours=1)
        elif timeframe == '4h':
            delta = timedelta(hours=4)
        elif timeframe == '1d':
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
            'XAU/USD': 1800.00,
            'AAPL': 180.00,
            'MSFT': 350.00,
            'GOOG': 140.00,
            'AMZN': 120.00,
            'TSLA': 200.00
        }
        
        # Use a reasonable base price or default to 100.0
        base_price = base_prices.get(symbol, 100.0)
        volatility = base_price * 0.002  # 0.2% volatility
        
        # Generate OHLC data
        import numpy as np
        np.random.seed(int(datetime.now().timestamp()) % 10000)  # Seed based on time for variety
        
        # Generate more realistic price movements with trends
        trend = np.random.choice([-1, 1]) * 0.0001  # Small trend component
        momentum = 0
        momentum_factor = 0.95  # How much momentum carries over
        
        closes = []
        current_price = base_price
        
        for i in range(count):
            # Update momentum with some mean reversion
            momentum = momentum_factor * momentum + np.random.normal(0, volatility)
            # Add trend and momentum to price
            current_price += trend + momentum
            closes.append(current_price)
        
        data = []
        
        for i, date in enumerate(dates):
            close = closes[i]
            # More realistic high/low based on volatility
            daily_volatility = volatility * np.random.uniform(0.5, 1.5)
            high = close + abs(np.random.normal(0, daily_volatility))
            low = close - abs(np.random.normal(0, daily_volatility))
            # Open should be close to previous close
            open_price = closes[i-1] if i > 0 else close + np.random.normal(0, volatility)
            
            # Ensure high is highest, low is lowest
            true_high = max(high, open_price, close)
            true_low = min(low, open_price, close)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': true_high,
                'low': true_low,
                'close': close,
                'volume': int(np.random.uniform(0.5, 1.5) * 1000)
            })
            
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
        
    def _get_simulated_current_price(self, symbol):
        """Generate a simulated current price for development mode"""
        # Base values for major pairs
        base_prices = {
            'EUR/USD': 1.1000,
            'GBP/USD': 1.3000,
            'USD/JPY': 115.00,
            'XAU/USD': 1800.00,
            'AAPL': 180.00,
            'MSFT': 350.00,
            'GOOG': 140.00,
            'AMZN': 120.00,
            'TSLA': 200.00
        }
        
        # Get base price or use default
        base_price = base_prices.get(symbol, 100.0)
        
        # Add small random variation
        import random
        variation = random.uniform(-0.001, 0.001)
        
        current_price = base_price + (base_price * variation)
        return current_price 