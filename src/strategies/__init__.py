"""
Trading strategies package initialization
"""
from .base_strategy import BaseStrategy
from .rsi_divergence import RSIDivergenceStrategy
from .breakout_detection import BreakoutDetectionStrategy
from .pattern_recognition import PatternRecognitionStrategy
from .kishoka_strategy import KishokaStrategy
from .moving_average_strategy import MovingAverageStrategy

# Export all strategies for easy import
__all__ = [
    'BaseStrategy',
    'RSIDivergenceStrategy',
    'BreakoutDetectionStrategy',
    'PatternRecognitionStrategy',
    'KishokaStrategy',
    'MovingAverageStrategy'
]
