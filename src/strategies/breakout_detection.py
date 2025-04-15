from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class BreakoutDetectionStrategy(BaseStrategy):
    """
    Breakout Detection Strategy
    Identifies key support/resistance levels and generates signals when price breaks through
    these levels with volume confirmation.
    """
    
    def __init__(self, 
                 lookback_period: int = 20,
                 volume_threshold: float = 1.5,
                 min_breakout_percentage: float = 0.02):
        super().__init__("Breakout Detection Strategy", {
            'lookback_period': lookback_period,
            'volume_threshold': volume_threshold,
            'min_breakout_percentage': min_breakout_percentage
        })
    
    def find_support_resistance(self, data: pd.DataFrame) -> Dict:
        """Find key support and resistance levels"""
        levels = {
            'support': [],
            'resistance': []
        }
        
        # Use rolling window to find local minima and maxima
        window = self.params['lookback_period']
        
        for i in range(window, len(data) - window):
            # Find support levels (local minima)
            if (data['low'].iloc[i] < data['low'].iloc[i-window:i]).all() and \
               (data['low'].iloc[i] < data['low'].iloc[i+1:i+window+1]).all():
                levels['support'].append({
                    'price': data['low'].iloc[i],
                    'timestamp': data.index[i]
                })
            
            # Find resistance levels (local maxima)
            if (data['high'].iloc[i] > data['high'].iloc[i-window:i]).all() and \
               (data['high'].iloc[i] > data['high'].iloc[i+1:i+window+1]).all():
                levels['resistance'].append({
                    'price': data['high'].iloc[i],
                    'timestamp': data.index[i]
                })
        
        return levels
    
    def detect_breakouts(self, data: pd.DataFrame, levels: Dict) -> List[Dict]:
        """Detect breakouts with volume confirmation"""
        breakouts = []
        avg_volume = data['volume'].rolling(window=self.params['lookback_period']).mean()
        
        for i in range(len(data)):
            current_price = data['close'].iloc[i]
            current_volume = data['volume'].iloc[i]
            
            # Check for resistance breakouts
            for level in levels['resistance']:
                if (current_price > level['price'] * (1 + self.params['min_breakout_percentage']) and
                    current_volume > avg_volume.iloc[i] * self.params['volume_threshold']):
                    breakouts.append({
                        'timestamp': data.index[i],
                        'type': 'bullish',
                        'breakout_price': current_price,
                        'level_price': level['price'],
                        'volume_ratio': current_volume / avg_volume.iloc[i],
                        'confidence': min(0.9, current_volume / (avg_volume.iloc[i] * 2))
                    })
            
            # Check for support breakouts
            for level in levels['support']:
                if (current_price < level['price'] * (1 - self.params['min_breakout_percentage']) and
                    current_volume > avg_volume.iloc[i] * self.params['volume_threshold']):
                    breakouts.append({
                        'timestamp': data.index[i],
                        'type': 'bearish',
                        'breakout_price': current_price,
                        'level_price': level['price'],
                        'volume_ratio': current_volume / avg_volume.iloc[i],
                        'confidence': min(0.9, current_volume / (avg_volume.iloc[i] * 2))
                    })
        
        return breakouts
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """Analyze market data for breakouts"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        levels = self.find_support_resistance(data)
        breakouts = self.detect_breakouts(data, levels)
        
        return {
            'support_levels': levels['support'],
            'resistance_levels': levels['resistance'],
            'breakouts': breakouts,
            'analysis_time': pd.Timestamp.now()
        }
    
    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """Generate trading signals based on breakouts"""
        analysis = self.analyze(data)
        signals = []
        
        for breakout in analysis['breakouts']:
            signal = {
                'timestamp': breakout['timestamp'],
                'type': 'buy' if breakout['type'] == 'bullish' else 'sell',
                'confidence': breakout['confidence'],
                'price': breakout['breakout_price'],
                'level_price': breakout['level_price'],
                'volume_ratio': breakout['volume_ratio'],
                'signal_type': 'breakout'
            }
            signals.append(signal)
        
        return signals
    
    def get_recommendation(self, data: pd.DataFrame) -> Dict:
        """Generate trading recommendation based on current market conditions"""
        signals = self.generate_signals(data)
        if not signals:
            return {
                'action': 'hold',
                'confidence': 0.5,
                'reason': 'No significant breakouts detected'
            }
        
        latest_signal = signals[-1]
        return {
            'action': latest_signal['type'],
            'confidence': latest_signal['confidence'],
            'price': latest_signal['price'],
            'level_price': latest_signal['level_price'],
            'volume_ratio': latest_signal['volume_ratio'],
            'reason': f'Breakout {latest_signal["type"]} signal with volume confirmation'
        } 