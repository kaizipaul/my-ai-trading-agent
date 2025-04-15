"""
Technical analysis utilities for calculating indicators
"""
import pandas as pd
import numpy as np
from termcolor import cprint
# Try to import pandas_ta, but provide fallbacks if it fails
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    
from src.config import MOVING_AVERAGES, RSI_PERIOD, MACD_SETTINGS

class TechnicalAnalysis:
    """Static class for technical analysis functions"""
    
    @staticmethod
    def add_all_indicators(df):
        """Add all technical indicators to a DataFrame"""
        if df is None or len(df) < 10:
            return df
            
        try:
            # Add Moving Averages
            df = TechnicalAnalysis.add_moving_averages(df)
            
            # Add RSI
            df = TechnicalAnalysis.add_rsi(df)
            
            # Add MACD
            df = TechnicalAnalysis.add_macd(df)
            
            # Add Bollinger Bands
            df = TechnicalAnalysis.add_bollinger_bands(df)
            
            # Add ATR
            df = TechnicalAnalysis.add_atr(df)
            
            # Add Stochastic
            df = TechnicalAnalysis.add_stochastic(df)
            
            return df
        except Exception as e:
            cprint(f"❌ Error adding indicators: {str(e)}", "red")
            return df
    
    @staticmethod
    def add_moving_averages(df):
        """Add moving averages to DataFrame"""
        # Simple Moving Averages
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_100'] = df['close'].rolling(window=100).mean()
        
        # Only calculate sma_200 if we have enough data
        if len(df) >= 200:
            df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['ema_10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_100'] = df['close'].ewm(span=100, adjust=False).mean()
        
        # Only calculate ema_200 if we have enough data
        if len(df) >= 200:
            df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        return df
    
    @staticmethod
    def add_rsi(df, period=14):
        """Add Relative Strength Index to DataFrame"""
        delta = df['close'].diff()
        
        # Get gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS
        rs = avg_gain / avg_loss.where(avg_loss != 0, 1)  # avoid division by zero
        
        # Calculate RSI
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    @staticmethod
    def add_macd(df, fast_period=12, slow_period=26, signal_period=9):
        """Add MACD to DataFrame"""
        # Calculate EMAs
        ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        df['macd'] = ema_fast - ema_slow
        
        # Calculate signal line
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    @staticmethod
    def add_bollinger_bands(df, period=20, std_dev=2):
        """Add Bollinger Bands to DataFrame"""
        # Calculate middle band (SMA)
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        
        # Calculate standard deviation
        rolling_std = df['close'].rolling(window=period).std()
        
        # Calculate upper and lower bands
        df['bb_upper'] = df['bb_middle'] + (rolling_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (rolling_std * std_dev)
        
        # Calculate bandwidth
        df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        return df
    
    @staticmethod
    def add_atr(df, period=14):
        """Add Average True Range to DataFrame"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate true range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.DataFrame([tr1, tr2, tr3]).max()
        
        # Calculate ATR
        df['atr'] = tr.rolling(window=period).mean()
        
        return df
    
    @staticmethod
    def add_stochastic(df, k_period=14, d_period=3):
        """Add Stochastic Oscillator to DataFrame"""
        # Calculate %K
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        
        df['stoch_k'] = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low).where(highest_high != lowest_low, 1))
        
        # Calculate %D
        df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()
        
        return df
    
    @staticmethod
    def is_golden_cross(df):
        """Check if a golden cross just occurred (short MA crossing above long MA)"""
        if 'sma_50' not in df.columns or 'sma_200' not in df.columns:
            return False
            
        # Check for sufficient data
        if df['sma_50'].isna().any() or df['sma_200'].isna().any():
            return False
            
        # Check if short MA just crossed above long MA
        prev_short_ma = df['sma_50'].iloc[-2]
        prev_long_ma = df['sma_200'].iloc[-2]
        curr_short_ma = df['sma_50'].iloc[-1]
        curr_long_ma = df['sma_200'].iloc[-1]
        
        return prev_short_ma < prev_long_ma and curr_short_ma > curr_long_ma
    
    @staticmethod
    def is_death_cross(df):
        """Check if a death cross just occurred (short MA crossing below long MA)"""
        if 'sma_50' not in df.columns or 'sma_200' not in df.columns:
            return False
            
        # Check for sufficient data
        if df['sma_50'].isna().any() or df['sma_200'].isna().any():
            return False
            
        # Check if short MA just crossed below long MA
        prev_short_ma = df['sma_50'].iloc[-2]
        prev_long_ma = df['sma_200'].iloc[-2]
        curr_short_ma = df['sma_50'].iloc[-1]
        curr_long_ma = df['sma_200'].iloc[-1]
        
        return prev_short_ma > prev_long_ma and curr_short_ma < curr_long_ma
    
    @staticmethod
    def calculate_support_resistance(df, window=20):
        """Calculate support and resistance levels"""
        if len(df) < window * 2:
            return None, None
            
        # Get local minima and maxima
        local_min = []
        local_max = []
        
        for i in range(window, len(df) - window):
            # Check for local minimum
            if all(df['low'].iloc[i] <= df['low'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['low'].iloc[i] <= df['low'].iloc[i+j] for j in range(1, window+1)):
                local_min.append(df['low'].iloc[i])
                
            # Check for local maximum
            if all(df['high'].iloc[i] >= df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['high'].iloc[i] >= df['high'].iloc[i+j] for j in range(1, window+1)):
                local_max.append(df['high'].iloc[i])
        
        # Calculate support (average of recent local minima)
        support = np.mean(local_min[-3:]) if len(local_min) >= 3 else None
        
        # Calculate resistance (average of recent local maxima)
        resistance = np.mean(local_max[-3:]) if len(local_max) >= 3 else None
        
        return support, resistance
