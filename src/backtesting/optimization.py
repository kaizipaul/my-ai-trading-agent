from typing import Dict, List, Optional, Union, Any, Callable
import pandas as pd
import numpy as np
from datetime import datetime
import itertools
from concurrent.futures import ProcessPoolExecutor
from ..strategies.base_strategy import BaseStrategy
from .backtest_engine import BacktestEngine

class StrategyOptimizer:
    """
    Optimizes strategy parameters using grid search or genetic algorithms.
    """
    
    def __init__(self, 
                 backtest_engine: BacktestEngine,
                 objective_function: str = 'sharpe_ratio'):
        """
        Initialize the optimizer.
        
        Args:
            backtest_engine: BacktestEngine instance
            objective_function: Metric to optimize ('sharpe_ratio', 'sortino_ratio', 'profit_factor')
        """
        self.backtest_engine = backtest_engine
        self.objective_function = objective_function
        self.best_params = None
        self.best_score = float('-inf')
        self.results = []
    
    def grid_search(self,
                   strategy_class: type,
                   param_grid: Dict[str, List[Any]],
                   symbol: str,
                   start_date: Union[str, datetime],
                   end_date: Union[str, datetime],
                   timeframe: str = '1d',
                   n_jobs: int = -1) -> Dict:
        """
        Perform grid search optimization.
        
        Args:
            strategy_class: Strategy class to optimize
            param_grid: Dictionary of parameters and their possible values
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            n_jobs: Number of parallel jobs (-1 for all cores)
            
        Returns:
            Dictionary containing optimization results
        """
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        # Run optimization in parallel
        with ProcessPoolExecutor(max_workers=n_jobs if n_jobs > 0 else None) as executor:
            futures = []
            for params in param_combinations:
                param_dict = dict(zip(param_names, params))
                futures.append(
                    executor.submit(
                        self._evaluate_params,
                        strategy_class,
                        param_dict,
                        symbol,
                        start_date,
                        end_date,
                        timeframe
                    )
                )
            
            # Collect results
            for future in futures:
                result = future.result()
                self.results.append(result)
                
                # Update best parameters
                if result['score'] > self.best_score:
                    self.best_score = result['score']
                    self.best_params = result['params']
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'all_results': self.results
        }
    
    def _evaluate_params(self,
                        strategy_class: type,
                        params: Dict[str, Any],
                        symbol: str,
                        start_date: Union[str, datetime],
                        end_date: Union[str, datetime],
                        timeframe: str) -> Dict:
        """
        Evaluate a set of parameters.
        
        Args:
            strategy_class: Strategy class
            params: Parameter dictionary
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            
        Returns:
            Dictionary containing evaluation results
        """
        # Create strategy instance with parameters
        strategy = strategy_class(**params)
        
        # Run backtest
        results = self.backtest_engine.run_backtest(
            strategy,
            symbol,
            start_date,
            end_date,
            timeframe
        )
        
        # Calculate score
        score = results['metrics'][self.objective_function]
        
        return {
            'params': params,
            'score': score,
            'results': results
        }

class MonteCarloSimulator:
    """
    Performs Monte Carlo simulations to stress-test strategies.
    """
    
    def __init__(self, backtest_engine: BacktestEngine):
        """
        Initialize the Monte Carlo simulator.
        
        Args:
            backtest_engine: BacktestEngine instance
        """
        self.backtest_engine = backtest_engine
        self.simulation_results = []
    
    def run_simulation(self,
                      strategy: BaseStrategy,
                      symbol: str,
                      start_date: Union[str, datetime],
                      end_date: Union[str, datetime],
                      timeframe: str = '1d',
                      n_simulations: int = 1000,
                      random_seed: Optional[int] = None) -> Dict:
        """
        Run Monte Carlo simulations.
        
        Args:
            strategy: Strategy instance
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            n_simulations: Number of simulations to run
            random_seed: Random seed for reproducibility
            
        Returns:
            Dictionary containing simulation results
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Load original data
        data = self.backtest_engine.data_manager.load_data(
            symbol, start_date, end_date, timeframe
        )
        data = self.backtest_engine.data_manager.preprocess_data(data)
        
        # Store simulation results
        equity_curves = []
        metrics = []
        
        for _ in range(n_simulations):
            # Generate random walk returns
            random_returns = self._generate_random_returns(data['returns'])
            
            # Create simulated price series
            simulated_prices = self._create_simulated_prices(data['close'].iloc[0], random_returns)
            
            # Create simulated data
            simulated_data = data.copy()
            simulated_data['close'] = simulated_prices
            simulated_data['open'] = simulated_prices * (1 + np.random.normal(0, 0.001, len(simulated_prices)))
            simulated_data['high'] = simulated_prices * (1 + np.abs(np.random.normal(0, 0.002, len(simulated_prices))))
            simulated_data['low'] = simulated_prices * (1 - np.abs(np.random.normal(0, 0.002, len(simulated_prices))))
            simulated_data['volume'] = data['volume'] * (1 + np.random.normal(0, 0.1, len(simulated_prices)))
            
            # Run backtest on simulated data
            results = self.backtest_engine.run_backtest(
                strategy,
                symbol,
                start_date,
                end_date,
                timeframe,
                data=simulated_data
            )
            
            equity_curves.append(results['equity_curve'])
            metrics.append(results['metrics'])
        
        # Calculate statistics
        equity_curves = np.array(equity_curves)
        final_equities = equity_curves[:, -1]
        
        stats = {
            'mean_final_equity': np.mean(final_equities),
            'std_final_equity': np.std(final_equities),
            'min_final_equity': np.min(final_equities),
            'max_final_equity': np.max(final_equities),
            'probability_of_loss': np.mean(final_equities < self.backtest_engine.initial_capital),
            'mean_sharpe_ratio': np.mean([m['sharpe_ratio'] for m in metrics]),
            'mean_max_drawdown': np.mean([m['max_drawdown'] for m in metrics]),
            'mean_win_rate': np.mean([m['win_rate'] for m in metrics])
        }
        
        self.simulation_results.append({
            'strategy': strategy.name,
            'symbol': symbol,
            'timeframe': timeframe,
            'n_simulations': n_simulations,
            'equity_curves': equity_curves,
            'metrics': metrics,
            'statistics': stats
        })
        
        return self.simulation_results[-1]
    
    def _generate_random_returns(self, original_returns: pd.Series) -> np.ndarray:
        """Generate random returns with similar statistical properties"""
        # Bootstrap returns with replacement
        return np.random.choice(original_returns, size=len(original_returns), replace=True)
    
    def _create_simulated_prices(self, 
                               initial_price: float, 
                               random_returns: np.ndarray) -> np.ndarray:
        """Create simulated price series from random returns"""
        prices = [initial_price]
        for ret in random_returns:
            prices.append(prices[-1] * (1 + ret))
        return np.array(prices)
    
    def plot_simulation_results(self, simulation_index: int = -1):
        """Plot Monte Carlo simulation results"""
        if not self.simulation_results:
            raise ValueError("No simulation results available")
        
        results = self.simulation_results[simulation_index]
        
        # Plot equity curves
        plt.figure(figsize=(12, 6))
        for curve in results['equity_curves']:
            plt.plot(curve, alpha=0.1, color='blue')
        
        # Plot mean equity curve
        mean_curve = np.mean(results['equity_curves'], axis=0)
        plt.plot(mean_curve, color='red', linewidth=2, label='Mean')
        
        plt.title(f"Monte Carlo Simulation - {results['strategy']}")
        plt.xlabel("Time")
        plt.ylabel("Equity")
        plt.grid(True)
        plt.legend()
        plt.show()
        
        # Plot distribution of final equity
        plt.figure(figsize=(12, 6))
        plt.hist(results['equity_curves'][:, -1], bins=50)
        plt.axvline(self.backtest_engine.initial_capital, color='red', linestyle='--', label='Initial Capital')
        plt.title(f"Final Equity Distribution - {results['strategy']}")
        plt.xlabel("Final Equity")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.legend()
        plt.show() 