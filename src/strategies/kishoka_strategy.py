"""
Kishoka Killswitch Strategy

A Fibonacci-based strategy that identifies swing points and uses retracement levels for trade signals.
"""
from src.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
import pandas as pd
from termcolor import cprint
from typing import Dict, List

class KishokaStrategy(BaseStrategy):
    def __init__(self, name: str = "Kishoka Killswitch Strategy", params: Dict = None):
        custom_params = {
            'swing_length': 14,
            'fib_levels': [0, 0.5, 1],
            'stop_loss_pips': 20,
            'profit_secure_pips': 50,
            'risk_free_offset': 20
        }
        
        if params:
            custom_params.update(params)
            
        super().__init__(name, custom_params)
        self.swing_length = custom_params['swing_length']
        self.fib_levels = custom_params['fib_levels']
        self.stop_loss_pips = custom_params['stop_loss_pips']
        self.profit_secure_pips = custom_params['profit_secure_pips']
        self.risk_free_offset = custom_params['risk_free_offset']
        
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Analyze market data using Kishoka strategy.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format for Kishoka strategy")
            
        # Determine pip size (default for most forex pairs)
        pip_size = 0.0001
        
        # Apply the Kishoka strategy analysis
        result = self._apply_kishoka_strategy(data, pip_size)
        
        # Extract key analysis points
        analysis_results = {
            'swing_highs': result['swing_high'].dropna().to_dict(),
            'swing_lows': result['swing_low'].dropna().to_dict(),
            'fibonacci_levels': {}
        }
        
        # Add fibonacci levels to results
        for level in self.fib_levels:
            level_name = f'fib_{int(level*100)}'
            if level_name in result:
                analysis_results['fibonacci_levels'][level_name] = result[level_name].dropna().to_dict()
                
        return analysis_results
    
    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on Kishoka strategy analysis.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            List of signal dictionaries with timestamp, type, and confidence
        """
        if not self.validate_data(data):
            return []
            
        # Default pip size
        pip_size = 0.0001
        
        # Apply strategy
        result = self._apply_kishoka_strategy(data, pip_size)
        
        # Extract signals
        signals = []
        
        for i in range(1, len(result)):
            # New position opened
            if result['position'].iloc[i] != 0 and result['position'].iloc[i-1] == 0:
                signal_type = 'buy' if result['position'].iloc[i] > 0 else 'sell'
                
                signals.append({
                    'timestamp': result.index[i],
                    'type': signal_type,
                    'confidence': 0.8,  # Default confidence
                    'price': result['entry_price'].iloc[i],
                    'stop_loss': result['stop_loss'].iloc[i],
                    'take_profit': result['take_profit'].iloc[i],
                    'signal_type': 'kishoka_fibonacci'
                })
                
        return signals
    
    def get_recommendation(self, data: pd.DataFrame) -> Dict:
        """
        Generate a trading recommendation based on current market conditions.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            Dictionary containing recommendation details
        """
        # Get the latest signals
        signals = self.generate_signals(data)
        
        # Default response if no signals
        if not signals:
            return {
                'action': 'hold',
                'confidence': 0.5,
                'reason': 'No Kishoka signals detected'
            }
        
        # Get the most recent signal
        latest_signal = signals[-1]
        latest_timestamp = latest_signal['timestamp']
        
        # Only recommend if signal is recent (within last 3 bars)
        if latest_timestamp >= data.index[-3]:
            return {
                'action': latest_signal['type'],
                'confidence': latest_signal['confidence'],
                'price': latest_signal['price'],
                'stop_loss': latest_signal['stop_loss'],
                'take_profit': latest_signal['take_profit'],
                'reason': f'Kishoka {latest_signal["type"]} signal at {latest_signal["price"]}'
            }
        else:
            return {
                'action': 'hold',
                'confidence': 0.5,
                'reason': 'No recent Kishoka signals'
            }
        
    def generate_signal(self, pair, data):
        """
        Generate trading signals based on Kishoka Killswitch strategy
        
        Args:
            pair (str): The trading symbol
            data (DataFrame): Price data with indicators
            
        Returns:
            dict: Signal information with direction, confidence, entry price, etc.
        """
        try:
            # Ensure we have enough data
            if data is None or len(data) < self.swing_length + 10:
                return None
                
            # Determine pip size based on instrument type
            pip_size = self._get_pip_size(pair)
            
            # Apply the Kishoka strategy
            result = self._apply_kishoka_strategy(data, pip_size)
            
            # Check if we have a new signal
            current_position = result['position'].iloc[-1]
            if current_position == 0:
                return None  # No active signal
                
            # Extract the most recent entry details
            entry_price = result['entry_price'].iloc[-1]
            stop_loss = result['stop_loss'].iloc[-1]
            take_profit = result['take_profit'].iloc[-1]
            
            # Determine direction
            direction = 'buy' if current_position > 0 else 'sell'
            
            # Calculate risk-reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(entry_price - take_profit)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Confidence score based on position size (handles partial closes)
            confidence = abs(current_position) if abs(current_position) <= 1 else 1.0
            
            # Create signal dictionary
            signal = {
                'direction': direction,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'signal_type': 'fibonacci_retracement',
                'metadata': {
                    'risk_reward_ratio': risk_reward,
                    'last_swing_high': result.get('swing_high', {}).iloc[-1] if 'swing_high' in result else None,
                    'last_swing_low': result.get('swing_low', {}).iloc[-1] if 'swing_low' in result else None,
                    'fib_levels': {f'fib_{int(level*100)}': result.get(f'fib_{int(level*100)}', {}).iloc[-1] 
                                  for level in self.fib_levels if f'fib_{int(level*100)}' in result}
                }
            }
            
            return signal
            
        except Exception as e:
            cprint(f"❌ Error generating Kishoka signals: {str(e)}", "red")
            return None
            
    def _get_pip_size(self, pair):
        """Determine pip size based on the instrument"""
        # For forex pairs, standard pip sizes
        if '/' in pair:
            if 'JPY' in pair:
                return 0.01  # For JPY pairs, pips are 0.01
            else:
                return 0.0001  # For most forex pairs, pips are 0.0001
        
        # For stocks, use a percentage of price
        return 0.01  # Default to 1 cent for stocks or other instruments
        
    def _apply_kishoka_strategy(self, df, pip_size=0.0001):
        """
        Apply the Kishoka Killswitch strategy logic
        
        Args:
            df (pd.DataFrame): OHLC data with datetime index
            pip_size (float): Value of 1 pip in price units
            
        Returns:
            pd.DataFrame: DataFrame with signals and positions
        """
        data = df.copy()
        data['position'] = 0  # 1 for long, -1 for short
        data['entry_price'] = np.nan
        data['stop_loss'] = np.nan
        data['take_profit'] = np.nan
        
        # Calculate swing highs and lows
        data['swing_high'] = data['high'].rolling(self.swing_length).max()
        data['swing_low'] = data['low'].rolling(self.swing_length).min()
        
        # Identify swing points
        data['is_swing_high'] = data['high'] >= data['swing_high']
        data['is_swing_low'] = data['low'] <= data['swing_low']
        
        # Track last valid swing points
        last_swing_high = np.nan
        last_swing_low = np.nan
        fib_range = 0
        
        # Fibonacci levels storage
        for level in self.fib_levels:
            data[f'fib_{int(level*100)}'] = np.nan
        
        for i in range(1, len(data)):
            # Update swing points
            if data['is_swing_high'].iloc[i]:
                last_swing_high = data['high'].iloc[i]
            if data['is_swing_low'].iloc[i]:
                last_swing_low = data['low'].iloc[i]
            
            # Calculate Fibonacci levels
            if not np.isnan(last_swing_high) and not np.isnan(last_swing_low):
                fib_range = last_swing_high - last_swing_low
                for level in self.fib_levels:
                    fib_value = last_swing_low + fib_range * level
                    data.loc[data.index[i], f'fib_{int(level*100)}'] = fib_value
            
            # Entry conditions
            current_low = data['low'].iloc[i]
            current_high = data['high'].iloc[i]
            close = data['close'].iloc[i]
            open_price = data['open'].iloc[i]
            
            # Check if Fibonacci levels are available
            if f'fib_0' in data.columns and i > 0:
                fib_0 = data['fib_0'].iloc[i]
                fib_50 = data['fib_50'].iloc[i] if 'fib_50' in data.columns else np.nan
                fib_100 = data['fib_100'].iloc[i] if 'fib_100' in data.columns else np.nan
                
                # Bullish rejection
                if (not np.isnan(fib_0) and 
                    current_low > fib_0 and 
                    close > open_price and 
                    close > fib_50 and 
                    data['position'].iloc[i-1] == 0):
                    
                    data.loc[data.index[i], 'position'] = 1
                    data.loc[data.index[i], 'entry_price'] = close
                    data.loc[data.index[i], 'stop_loss'] = last_swing_low - (self.stop_loss_pips * pip_size)
                    data.loc[data.index[i], 'take_profit'] = close + (self.profit_secure_pips * pip_size)
                
                # Bearish rejection
                elif (not np.isnan(fib_100) and 
                     current_high < fib_100 and 
                     close < open_price and 
                     close < fib_50 and 
                     data['position'].iloc[i-1] == 0):
                    
                    data.loc[data.index[i], 'position'] = -1
                    data.loc[data.index[i], 'entry_price'] = close
                    data.loc[data.index[i], 'stop_loss'] = last_swing_high + (self.stop_loss_pips * pip_size)
                    data.loc[data.index[i], 'take_profit'] = close - (self.profit_secure_pips * pip_size)
            
            # Risk management - copy from previous position if no new entry
            elif data['position'].iloc[i-1] != 0 and data['position'].iloc[i] == 0:
                data.loc[data.index[i], 'position'] = data['position'].iloc[i-1]
                data.loc[data.index[i], 'entry_price'] = data['entry_price'].iloc[i-1]
                data.loc[data.index[i], 'stop_loss'] = data['stop_loss'].iloc[i-1]
                data.loc[data.index[i], 'take_profit'] = data['take_profit'].iloc[i-1]
                
                # Current values for risk management
                entry = data['entry_price'].iloc[i]
                current_close = data['close'].iloc[i]
                
                # Move to breakeven
                if entry is not None and not np.isnan(entry):
                    if abs(current_close - entry) >= self.risk_free_offset * pip_size:
                        data.loc[data.index[i], 'stop_loss'] = entry
                    
                # Partial close at 50% level if we have the Fibonacci levels
                if not np.isnan(fib_50):
                    if ((data['position'].iloc[i] == 1 and current_close >= fib_50) or 
                        (data['position'].iloc[i] == -1 and current_close <= fib_50)):
                        # Scale position size down to 0.5 (partial close)
                        data.loc[data.index[i], 'position'] = data['position'].iloc[i] * 0.5
                    
                # Check stop loss and take profit
                sl = data['stop_loss'].iloc[i]
                tp = data['take_profit'].iloc[i]
                
                if not np.isnan(sl) and not np.isnan(tp):
                    if ((data['position'].iloc[i] == 1 and (current_close <= sl or current_close >= tp)) or
                        (data['position'].iloc[i] == -1 and (current_close >= sl or current_close <= tp))):
                        data.loc[data.index[i], 'position'] = 0  # Close position
        
        return data 