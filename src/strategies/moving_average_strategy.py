"""
Moving Average Crossover Strategy
"""
from src.strategies.base_strategy import BaseStrategy
from src.config import MOVING_AVERAGES
import pandas as pd
import numpy as np
from typing import Dict, List

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, name: str = "Moving Average Strategy", params: Dict = None):
        custom_params = {
            'fast_period': 20,
            'slow_period': 50,
            'stop_loss_multiplier': 2.0,
            'take_profit_multiplier': 3.0
        }
        
        if params:
            custom_params.update(params)
            
        super().__init__(name, custom_params)
        
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Analyze market data using Moving Average strategy.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format for Moving Average strategy")
            
        # Calculate moving averages if not already in data
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        
        fast_ma_col = f'sma_{fast_period}'
        slow_ma_col = f'sma_{slow_period}'
        
        result = data.copy()
        
        if fast_ma_col not in result.columns:
            result[fast_ma_col] = result['close'].rolling(window=fast_period).mean()
            
        if slow_ma_col not in result.columns:
            result[slow_ma_col] = result['close'].rolling(window=slow_period).mean()
            
        # Calculate ATR if not available
        if 'atr' not in result.columns:
            # Simple ATR calculation using True Range
            high_low = result['high'] - result['low']
            high_close = (result['high'] - result['close'].shift(1)).abs()
            low_close = (result['low'] - result['close'].shift(1)).abs()
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            result['atr'] = true_range.rolling(window=14).mean()
        
        # Identify crossovers
        result['fast_ma_above'] = result[fast_ma_col] > result[slow_ma_col]
        result['crossover'] = result['fast_ma_above'] != result['fast_ma_above'].shift(1)
        result['bullish_crossover'] = result['crossover'] & result['fast_ma_above']
        result['bearish_crossover'] = result['crossover'] & ~result['fast_ma_above']
        
        # Calculate price relative to MAs
        result['price_vs_fast_ma'] = result['close'] - result[fast_ma_col]
        result['price_vs_slow_ma'] = result['close'] - result[slow_ma_col]
        result['price_vs_slow_ma_pct'] = result['price_vs_slow_ma'] / result['close']
        
        return {
            'fast_ma': result[fast_ma_col].to_dict(),
            'slow_ma': result[slow_ma_col].to_dict(),
            'bullish_crossovers': result.loc[result['bullish_crossover']].index.tolist(),
            'bearish_crossovers': result.loc[result['bearish_crossover']].index.tolist(),
            'atr': result['atr'].to_dict(),
            'analysis_data': result
        }
    
    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on Moving Average strategy analysis.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            List of signal dictionaries with timestamp, type, and confidence
        """
        if not self.validate_data(data):
            return []
            
        analysis = self.analyze(data)
        result = analysis['analysis_data']
        signals = []
        
        # Configure multipliers from params
        stop_loss_multiplier = self.params['stop_loss_multiplier']
        take_profit_multiplier = self.params['take_profit_multiplier']
        
        # Generate signals for each crossover
        for i in range(1, len(result)):
            # Skip if we don't have valid ATR
            if pd.isna(result['atr'].iloc[i]):
                continue
                
            close_price = result['close'].iloc[i]
            atr = result['atr'].iloc[i]
            
            # Bullish crossover signal
            if result['bullish_crossover'].iloc[i]:
                signals.append({
                    'timestamp': result.index[i],
                    'type': 'buy',
                    'confidence': 0.8,
                    'price': close_price,
                    'stop_loss': close_price - (atr * stop_loss_multiplier),
                    'take_profit': close_price + (atr * take_profit_multiplier),
                    'signal_type': 'ma_bullish_crossover'
                })
            
            # Bearish crossover signal
            elif result['bearish_crossover'].iloc[i]:
                signals.append({
                    'timestamp': result.index[i],
                    'type': 'sell',
                    'confidence': 0.8,
                    'price': close_price,
                    'stop_loss': close_price + (atr * stop_loss_multiplier),
                    'take_profit': close_price - (atr * take_profit_multiplier),
                    'signal_type': 'ma_bearish_crossover'
                })
            
            # Strong trend continuation signals
            elif (result['fast_ma_above'].iloc[i] and 
                  result['price_vs_fast_ma'].iloc[i] > 0 and 
                  result['price_vs_slow_ma_pct'].iloc[i] > 0.02):
                signals.append({
                    'timestamp': result.index[i],
                    'type': 'buy',
                    'confidence': 0.6,
                    'price': close_price,
                    'stop_loss': close_price - (atr * stop_loss_multiplier),
                    'take_profit': close_price + (atr * take_profit_multiplier),
                    'signal_type': 'strong_uptrend'
                })
            
            elif (not result['fast_ma_above'].iloc[i] and 
                  result['price_vs_fast_ma'].iloc[i] < 0 and 
                  result['price_vs_slow_ma_pct'].iloc[i] < -0.02):
                signals.append({
                    'timestamp': result.index[i],
                    'type': 'sell',
                    'confidence': 0.6,
                    'price': close_price,
                    'stop_loss': close_price + (atr * stop_loss_multiplier),
                    'take_profit': close_price - (atr * take_profit_multiplier),
                    'signal_type': 'strong_downtrend'
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
        # Get signals
        signals = self.generate_signals(data)
        
        # Default recommendation
        if not signals:
            return {
                'action': 'hold',
                'confidence': 0.5,
                'reason': 'No significant moving average signals'
            }
        
        # Get most recent signal
        latest_signal = signals[-1]
        latest_timestamp = latest_signal['timestamp']
        
        # Only recommend if signal is recent (within last 2 bars)
        if latest_timestamp >= data.index[-2]:
            return {
                'action': latest_signal['type'],
                'confidence': latest_signal['confidence'],
                'price': latest_signal['price'],
                'stop_loss': latest_signal['stop_loss'],
                'take_profit': latest_signal['take_profit'],
                'reason': f"Moving Average {latest_signal['signal_type']} signal"
            }
        else:
            return {
                'action': 'hold',
                'confidence': 0.5,
                'reason': 'No recent moving average signals'
            }
        
    def generate_signal(self, pair, data):
        """Generate signals based on MA crossover"""
        try:
            # Ensure we have enough data points
            if len(data) < 50:
                return None
                
            # We'll use short and medium term MAs for crossover strategy
            fast_period = 20  # 20-day MA
            slow_period = 50  # 50-day MA
            
            # Get latest values - use the columns added by TechnicalAnalysis
            fast_ma_col = f'sma_{fast_period}'
            slow_ma_col = f'sma_{slow_period}'
            
            if fast_ma_col not in data.columns or slow_ma_col not in data.columns:
                return None
                
            fast_ma = data[fast_ma_col].iloc[-1]
            slow_ma = data[slow_ma_col].iloc[-1]
            prev_fast = data[fast_ma_col].iloc[-2]
            prev_slow = data[slow_ma_col].iloc[-2]
            
            # Close price for entry
            close_price = data['close'].iloc[-1]
            
            # Calculate ATR for stop loss/take profit
            atr = data['atr'].iloc[-1] if 'atr' in data.columns else None
            
            # Default ATR value if not available
            if atr is None or pd.isna(atr):
                # Approximate ATR as a percentage of price
                atr = close_price * 0.015  # 1.5% of price as default ATR
            
            # Calculate stop loss and take profit based on ATR
            stop_loss_multiplier = 2.0
            take_profit_multiplier = 3.0
            
            # Check for bullish crossover (fast MA crossing above slow MA)
            if fast_ma > slow_ma and prev_fast <= prev_slow:
                return {
                    'direction': 'buy',
                    'confidence': 0.8,
                    'entry_price': close_price,
                    'stop_loss': close_price - (atr * stop_loss_multiplier),
                    'take_profit': close_price + (atr * take_profit_multiplier),
                    'signal_type': 'bullish_crossover',
                    'metadata': {
                        'fast_ma': fast_ma,
                        'slow_ma': slow_ma,
                        'fast_period': fast_period,
                        'slow_period': slow_period
                    }
                }
            # Check for bearish crossover (fast MA crossing below slow MA)
            elif fast_ma < slow_ma and prev_fast >= prev_slow:
                return {
                    'direction': 'sell',
                    'confidence': 0.8,
                    'entry_price': close_price,
                    'stop_loss': close_price + (atr * stop_loss_multiplier),
                    'take_profit': close_price - (atr * take_profit_multiplier),
                    'signal_type': 'bearish_crossover',
                    'metadata': {
                        'fast_ma': fast_ma,
                        'slow_ma': slow_ma,
                        'fast_period': fast_period,
                        'slow_period': slow_period
                    }
                }
            
            # No crossover, check for price significantly above/below MAs
            price_vs_fast = close_price - fast_ma
            price_vs_slow = close_price - slow_ma
            
            # Strong trend continuation signals
            if fast_ma > slow_ma and price_vs_fast > 0 and price_vs_slow / close_price > 0.02:
                # Price well above both MAs in uptrend
                return {
                    'direction': 'buy',
                    'confidence': 0.6,
                    'entry_price': close_price,
                    'stop_loss': close_price - (atr * stop_loss_multiplier),
                    'take_profit': close_price + (atr * take_profit_multiplier),
                    'signal_type': 'strong_uptrend',
                    'metadata': {
                        'price_vs_slow_ma_pct': price_vs_slow / close_price
                    }
                }
            elif fast_ma < slow_ma and price_vs_fast < 0 and price_vs_slow / close_price < -0.02:
                # Price well below both MAs in downtrend
                return {
                    'direction': 'sell',
                    'confidence': 0.6,
                    'entry_price': close_price,
                    'stop_loss': close_price + (atr * stop_loss_multiplier),
                    'take_profit': close_price - (atr * take_profit_multiplier),
                    'signal_type': 'strong_downtrend',
                    'metadata': {
                        'price_vs_slow_ma_pct': price_vs_slow / close_price
                    }
                }
                
            return None
            
        except Exception as e:
            print(f"❌ Error generating MA signals: {str(e)}")
            return None