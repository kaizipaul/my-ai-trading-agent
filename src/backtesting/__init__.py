"""
Backtesting package for evaluating trading strategies.
"""
from .backtest_engine import BacktestEngine
from .optimization import StrategyOptimizer, MonteCarloSimulator

__all__ = [
    'BacktestEngine',
    'StrategyOptimizer',
    'MonteCarloSimulator'
] 