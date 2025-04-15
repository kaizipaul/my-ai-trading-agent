from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
import os
import pickle
from datetime import datetime, timedelta
import logging

class HistoricalDataManager:
    """
    Manages historical price data for backtesting and analysis.
    Handles data fetching, caching, and preprocessing.
    """
    
    def __init__(self, data_dir: str = "data/historical", cache_dir: str = "data/cache"):
        """
        Initialize the historical data manager.
        
        Args:
            data_dir: Directory for storing raw historical data
            cache_dir: Directory for storing processed/cached data
        """
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        self.cache = {}
        self.logger = logging.getLogger(__name__)
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
    
    def load_data(self, 
                 symbol: str, 
                 start_date: Union[str, datetime], 
                 end_date: Union[str, datetime],
                 timeframe: str = '1d',
                 force_refresh: bool = False) -> pd.DataFrame:
        """
        Load historical data for a symbol and timeframe.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD')
            start_date: Start date for data
            end_date: End date for data
            timeframe: Data timeframe (e.g., '1d', '1h', '15m')
            force_refresh: Whether to force refresh from source
            
        Returns:
            DataFrame containing historical price data
        """
        cache_key = f"{symbol}_{timeframe}_{start_date}_{end_date}"
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try to load from cache file
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if not force_refresh and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                self.cache[cache_key] = data
                return data
            except Exception as e:
                self.logger.warning(f"Error loading cache file: {e}")
        
        # Load or fetch data
        data = self._fetch_data(symbol, start_date, end_date, timeframe)
        
        # Cache the data
        self.cache[cache_key] = data
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        
        return data
    
    def _fetch_data(self, 
                   symbol: str, 
                   start_date: Union[str, datetime], 
                   end_date: Union[str, datetime],
                   timeframe: str) -> pd.DataFrame:
        """
        Fetch data from source or local storage.
        This is a placeholder - implement actual data fetching logic.
        """
        # Convert dates to datetime if they're strings
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # Check local storage first
        local_file = os.path.join(self.data_dir, f"{symbol}_{timeframe}.csv")
        if os.path.exists(local_file):
            data = pd.read_csv(local_file, index_col=0, parse_dates=True)
            data = data.loc[start_date:end_date]
            return data
        
        # TODO: Implement actual data fetching from exchange API
        # For now, return empty DataFrame with required columns
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess historical data for analysis.
        
        Args:
            data: Raw price data
            
        Returns:
            Preprocessed DataFrame
        """
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")
        
        # Sort by index
        data = data.sort_index()
        
        # Remove duplicates
        data = data[~data.index.duplicated(keep='first')]
        
        # Fill missing values
        data = data.fillna(method='ffill')
        
        # Calculate returns
        data['returns'] = data['close'].pct_change()
        
        # Calculate log returns
        data['log_returns'] = np.log(data['close'] / data['close'].shift(1))
        
        return data
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols in local storage"""
        files = os.listdir(self.data_dir)
        symbols = set()
        for file in files:
            if file.endswith('.csv'):
                symbol = file.split('_')[0]
                symbols.add(symbol)
        return list(symbols)
    
    def get_available_timeframes(self, symbol: str) -> List[str]:
        """Get list of available timeframes for a symbol"""
        files = os.listdir(self.data_dir)
        timeframes = set()
        for file in files:
            if file.startswith(f"{symbol}_"):
                timeframe = file.split('_')[1].split('.')[0]
                timeframes.add(timeframe)
        return list(timeframes)
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache = {}
        for file in os.listdir(self.cache_dir):
            if file.endswith('.pkl'):
                os.remove(os.path.join(self.cache_dir, file)) 