from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from ..strategies.base_strategy import BaseStrategy
from ..data.historical_data_manager import HistoricalDataManager

class BacktestEngine:
    """
    Backtesting engine for evaluating trading strategies.
    Handles strategy execution, performance calculation, and visualization.
    """
    
    def __init__(self, 
                 data_manager: HistoricalDataManager,
                 initial_capital: float = 10000.0,
                 commission: float = 0.001):
        """
        Initialize the backtesting engine.
        
        Args:
            data_manager: HistoricalDataManager instance
            initial_capital: Initial capital for backtesting
            commission: Trading commission rate
        """
        self.data_manager = data_manager
        self.initial_capital = initial_capital
        self.commission = commission
        self.results = {}
        self.trades = []
        
    def run_backtest(self,
                    strategy: BaseStrategy,
                    symbol: str,
                    start_date: Union[str, datetime],
                    end_date: Union[str, datetime],
                    timeframe: str = '1d') -> Dict:
        """
        Run a backtest for a strategy.
        
        Args:
            strategy: Strategy instance to backtest
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            
        Returns:
            Dictionary containing backtest results
        """
        # Load and preprocess data
        data = self.data_manager.load_data(symbol, start_date, end_date, timeframe)
        data = self.data_manager.preprocess_data(data)
        
        # Initialize backtest variables
        capital = self.initial_capital
        position = 0
        trades = []
        equity_curve = []
        
        # Run strategy on each bar
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            
            # Get strategy recommendation
            recommendation = strategy.get_recommendation(current_data)
            
            # Execute trade if signal is generated
            if recommendation['action'] != 'hold':
                price = data['close'].iloc[i]
                
                # Calculate position size
                if recommendation['action'] == 'buy' and position <= 0:
                    position_size = capital / price
                    position = position_size
                    capital -= position_size * price * (1 + self.commission)
                    trades.append({
                        'timestamp': data.index[i],
                        'type': 'buy',
                        'price': price,
                        'size': position_size,
                        'capital': capital
                    })
                elif recommendation['action'] == 'sell' and position > 0:
                    capital += position * price * (1 - self.commission)
                    trades.append({
                        'timestamp': data.index[i],
                        'type': 'sell',
                        'price': price,
                        'size': position,
                        'capital': capital
                    })
                    position = 0
            
            # Update equity curve
            current_equity = capital + (position * data['close'].iloc[i] if position > 0 else 0)
            equity_curve.append(current_equity)
        
        # Calculate performance metrics
        equity_series = pd.Series(equity_curve, index=data.index)
        returns = equity_series.pct_change().dropna()
        
        # Store results
        self.results = {
            'strategy': strategy.name,
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_capital': equity_curve[-1],
            'total_return': (equity_curve[-1] / self.initial_capital) - 1,
            'trades': trades,
            'equity_curve': equity_curve,
            'returns': returns,
            'metrics': self._calculate_metrics(returns, trades)
        }
        
        return self.results
    
    def _calculate_metrics(self, returns: pd.Series, trades: List[Dict]) -> Dict:
        """Calculate performance metrics"""
        if len(trades) < 2:
            return {
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_trade': 0
            }
        
        # Calculate returns-based metrics
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
        downside_returns = returns[returns < 0]
        sortino_ratio = np.sqrt(252) * returns.mean() / downside_returns.std() if len(downside_returns) > 0 else 0
        
        # Calculate drawdown
        cummax = returns.cumsum().expanding().max()
        drawdown = (returns.cumsum() - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # Calculate trade-based metrics
        winning_trades = [t for t in trades if t['type'] == 'sell' and t['capital'] > trades[trades.index(t)-1]['capital']]
        losing_trades = [t for t in trades if t['type'] == 'sell' and t['capital'] <= trades[trades.index(t)-1]['capital']]
        
        win_rate = len(winning_trades) / len([t for t in trades if t['type'] == 'sell'])
        
        total_profit = sum(t['capital'] - trades[trades.index(t)-1]['capital'] for t in winning_trades)
        total_loss = abs(sum(t['capital'] - trades[trades.index(t)-1]['capital'] for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        avg_trade = (total_profit - total_loss) / len([t for t in trades if t['type'] == 'sell'])
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_trade': avg_trade
        }
    
    def plot_equity_curve(self):
        """Plot the equity curve"""
        if not self.results:
            raise ValueError("No backtest results available")
        
        plt.figure(figsize=(12, 6))
        plt.plot(self.results['equity_curve'])
        plt.title(f"Equity Curve - {self.results['strategy']}")
        plt.xlabel("Date")
        plt.ylabel("Equity")
        plt.grid(True)
        plt.show()
    
    def plot_trade_distribution(self):
        """Plot the distribution of trade returns"""
        if not self.results:
            raise ValueError("No backtest results available")
        
        trades = self.results['trades']
        returns = []
        
        for i in range(1, len(trades)):
            if trades[i]['type'] == 'sell':
                trade_return = (trades[i]['capital'] - trades[i-1]['capital']) / trades[i-1]['capital']
                returns.append(trade_return)
        
        plt.figure(figsize=(12, 6))
        sns.histplot(returns, bins=50)
        plt.title(f"Trade Return Distribution - {self.results['strategy']}")
        plt.xlabel("Return")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.show()
    
    def get_summary(self) -> Dict:
        """Get a summary of the backtest results"""
        if not self.results:
            raise ValueError("No backtest results available")
        
        return {
            'Strategy': self.results['strategy'],
            'Symbol': self.results['symbol'],
            'Timeframe': self.results['timeframe'],
            'Period': f"{self.results['start_date']} to {self.results['end_date']}",
            'Initial Capital': f"${self.results['initial_capital']:,.2f}",
            'Final Capital': f"${self.results['final_capital']:,.2f}",
            'Total Return': f"{self.results['total_return']*100:.2f}%",
            'Sharpe Ratio': f"{self.results['metrics']['sharpe_ratio']:.2f}",
            'Sortino Ratio': f"{self.results['metrics']['sortino_ratio']:.2f}",
            'Max Drawdown': f"{self.results['metrics']['max_drawdown']*100:.2f}%",
            'Win Rate': f"{self.results['metrics']['win_rate']*100:.2f}%",
            'Profit Factor': f"{self.results['metrics']['profit_factor']:.2f}",
            'Average Trade': f"${self.results['metrics']['avg_trade']:,.2f}",
            'Total Trades': len([t for t in self.results['trades'] if t['type'] == 'sell'])
        } 