from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class RSIDivergenceStrategy(BaseStrategy):
    """
    RSI Divergence Strategy
    Detects when price makes higher lows but RSI makes lower lows (or vice versa)
    and generates signals at these divergence points.
    """
    
    def __init__(self, rsi_period: int = 14, divergence_threshold: float = 0.1):
        super().__init__("RSI Divergence Strategy", {
            'rsi_period': rsi_period,
            'divergence_threshold': divergence_threshold
        })
        
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def find_divergences(self, data: pd.DataFrame, rsi: pd.Series) -> List[Dict]:
        """Find bullish and bearish divergences"""
        divergences = []
        window = 5  # Lookback window for finding peaks/troughs
        
        for i in range(window, len(data) - window):
            # Find local minima in price and RSI
            if (data['low'].iloc[i] < data['low'].iloc[i-window:i]).all() and \
               (data['low'].iloc[i] < data['low'].iloc[i+1:i+window+1]).all():
                # Bullish divergence: Higher lows in price, lower lows in RSI
                if (rsi.iloc[i] < rsi.iloc[i-window:i]).all() and \
                   (rsi.iloc[i] < rsi.iloc[i+1:i+window+1]).all():
                    divergences.append({
                        'timestamp': data.index[i],
                        'type': 'bullish',
                        'price_low': data['low'].iloc[i],
                        'rsi_low': rsi.iloc[i],
                        'confidence': 0.7
                    })
            
            # Find local maxima in price and RSI
            if (data['high'].iloc[i] > data['high'].iloc[i-window:i]).all() and \
               (data['high'].iloc[i] > data['high'].iloc[i+1:i+window+1]).all():
                # Bearish divergence: Lower highs in price, higher highs in RSI
                if (rsi.iloc[i] > rsi.iloc[i-window:i]).all() and \
                   (rsi.iloc[i] > rsi.iloc[i+1:i+window+1]).all():
                    divergences.append({
                        'timestamp': data.index[i],
                        'type': 'bearish',
                        'price_high': data['high'].iloc[i],
                        'rsi_high': rsi.iloc[i],
                        'confidence': 0.7
                    })
        
        return divergences
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """Analyze market data for RSI divergences"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        rsi = self.calculate_rsi(data)
        divergences = self.find_divergences(data, rsi)
        
        return {
            'rsi_values': rsi,
            'divergences': divergences,
            'analysis_time': pd.Timestamp.now()
        }
    
    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """Generate trading signals based on RSI divergences"""
        analysis = self.analyze(data)
        signals = []
        
        for div in analysis['divergences']:
            signal = {
                'timestamp': div['timestamp'],
                'type': 'buy' if div['type'] == 'bullish' else 'sell',
                'confidence': div['confidence'],
                'price': div['price_low'] if div['type'] == 'bullish' else div['price_high'],
                'rsi_value': div['rsi_low'] if div['type'] == 'bullish' else div['rsi_high'],
                'signal_type': 'rsi_divergence'
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
                'reason': 'No significant divergences detected'
            }
        
        latest_signal = signals[-1]
        return {
            'action': latest_signal['type'],
            'confidence': latest_signal['confidence'],
            'price': latest_signal['price'],
            'rsi_value': latest_signal['rsi_value'],
            'reason': f'RSI {latest_signal["type"]} divergence detected'
        } 