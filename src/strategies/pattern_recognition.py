from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class PatternRecognitionStrategy(BaseStrategy):
    """
    Pattern Recognition Strategy
    Implements algorithms to detect common chart patterns (head & shoulders, double tops, etc.)
    and uses pattern completion to generate entry/exit signals.
    """
    
    def __init__(self, 
                 min_pattern_length: int = 20,
                 max_pattern_length: int = 100,
                 pattern_threshold: float = 0.02):
        super().__init__("Pattern Recognition Strategy", {
            'min_pattern_length': min_pattern_length,
            'max_pattern_length': max_pattern_length,
            'pattern_threshold': pattern_threshold
        })
    
    def find_local_extrema(self, data: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """Find local minima and maxima in the price data"""
        peaks = []
        troughs = []
        window = 5  # Lookback window for finding extrema
        
        for i in range(window, len(data) - window):
            # Find peaks
            if (data['high'].iloc[i] > data['high'].iloc[i-window:i]).all() and \
               (data['high'].iloc[i] > data['high'].iloc[i+1:i+window+1]).all():
                peaks.append({
                    'index': i,
                    'price': data['high'].iloc[i],
                    'timestamp': data.index[i]
                })
            
            # Find troughs
            if (data['low'].iloc[i] < data['low'].iloc[i-window:i]).all() and \
               (data['low'].iloc[i] < data['low'].iloc[i+1:i+window+1]).all():
                troughs.append({
                    'index': i,
                    'price': data['low'].iloc[i],
                    'timestamp': data.index[i]
                })
        
        return peaks, troughs
    
    def detect_head_and_shoulders(self, peaks: List[Dict], troughs: List[Dict]) -> List[Dict]:
        """Detect head and shoulders patterns"""
        patterns = []
        
        for i in range(2, len(peaks) - 2):
            # Check for head and shoulders pattern
            left_shoulder = peaks[i-1]
            head = peaks[i]
            right_shoulder = peaks[i+1]
            
            # Check if head is higher than shoulders
            if (head['price'] > left_shoulder['price'] and 
                head['price'] > right_shoulder['price']):
                
                # Check if shoulders are roughly at same level
                shoulder_diff = abs(left_shoulder['price'] - right_shoulder['price'])
                if shoulder_diff < self.params['pattern_threshold'] * head['price']:
                    patterns.append({
                        'type': 'head_and_shoulders',
                        'direction': 'bearish',
                        'head': head,
                        'left_shoulder': left_shoulder,
                        'right_shoulder': right_shoulder,
                        'neckline': min(troughs[i-1]['price'], troughs[i]['price']),
                        'confidence': 0.8
                    })
        
        return patterns
    
    def detect_double_top_bottom(self, peaks: List[Dict], troughs: List[Dict]) -> List[Dict]:
        """Detect double top and double bottom patterns"""
        patterns = []
        
        # Check for double tops
        for i in range(1, len(peaks) - 1):
            if abs(peaks[i]['price'] - peaks[i+1]['price']) < self.params['pattern_threshold'] * peaks[i]['price']:
                patterns.append({
                    'type': 'double_top',
                    'direction': 'bearish',
                    'first_top': peaks[i],
                    'second_top': peaks[i+1],
                    'trough': troughs[i],
                    'confidence': 0.7
                })
        
        # Check for double bottoms
        for i in range(1, len(troughs) - 1):
            if abs(troughs[i]['price'] - troughs[i+1]['price']) < self.params['pattern_threshold'] * troughs[i]['price']:
                patterns.append({
                    'type': 'double_bottom',
                    'direction': 'bullish',
                    'first_bottom': troughs[i],
                    'second_bottom': troughs[i+1],
                    'peak': peaks[i],
                    'confidence': 0.7
                })
        
        return patterns
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """Analyze market data for chart patterns"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        peaks, troughs = self.find_local_extrema(data)
        head_and_shoulders = self.detect_head_and_shoulders(peaks, troughs)
        double_patterns = self.detect_double_top_bottom(peaks, troughs)
        
        return {
            'peaks': peaks,
            'troughs': troughs,
            'head_and_shoulders': head_and_shoulders,
            'double_patterns': double_patterns,
            'analysis_time': pd.Timestamp.now()
        }
    
    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """Generate trading signals based on pattern recognition"""
        analysis = self.analyze(data)
        signals = []
        
        # Process head and shoulders patterns
        for pattern in analysis['head_and_shoulders']:
            signals.append({
                'timestamp': pattern['right_shoulder']['timestamp'],
                'type': 'sell' if pattern['direction'] == 'bearish' else 'buy',
                'confidence': pattern['confidence'],
                'price': pattern['right_shoulder']['price'],
                'pattern_type': pattern['type'],
                'neckline': pattern['neckline']
            })
        
        # Process double top/bottom patterns
        for pattern in analysis['double_patterns']:
            signals.append({
                'timestamp': pattern['second_top']['timestamp'] if pattern['type'] == 'double_top' else pattern['second_bottom']['timestamp'],
                'type': 'sell' if pattern['direction'] == 'bearish' else 'buy',
                'confidence': pattern['confidence'],
                'price': pattern['second_top']['price'] if pattern['type'] == 'double_top' else pattern['second_bottom']['price'],
                'pattern_type': pattern['type']
            })
        
        return signals
    
    def get_recommendation(self, data: pd.DataFrame) -> Dict:
        """Generate trading recommendation based on current market conditions"""
        signals = self.generate_signals(data)
        if not signals:
            return {
                'action': 'hold',
                'confidence': 0.5,
                'reason': 'No significant patterns detected'
            }
        
        latest_signal = signals[-1]
        return {
            'action': latest_signal['type'],
            'confidence': latest_signal['confidence'],
            'price': latest_signal['price'],
            'pattern_type': latest_signal['pattern_type'],
            'reason': f'{latest_signal["pattern_type"]} pattern detected'
        } 