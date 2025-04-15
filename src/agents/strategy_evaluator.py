"""
AI-powered forex strategy evaluator
"""
import json
from termcolor import cprint
import anthropic
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from ..backtesting import BacktestEngine, StrategyOptimizer, MonteCarloSimulator

# Strategy Evaluation Prompt for Forex
FOREX_EVAL_PROMPT = """
You are a Forex Trading Strategy Validator 📊

Analyze the following trading signals and market conditions:

Strategy Signals:
{strategy_signals}

Market Context:
- Pair: {pair}
- Current Price: {current_price}
- Technical Indicators: {technical_data}
- News Sentiment: {sentiment_data}

Your task:
1. Evaluate each strategy signal's validity
2. Check alignment with:
   - Technical indicators
   - Market sentiment
   - Current market conditions
   - Risk parameters
3. Look for confirmation/contradiction between strategies
4. Consider:
   - Trend direction
   - Support/resistance levels
   - Volume profile
   - Market volatility
   - Economic calendar events

Respond in this format:
1. First line: EXECUTE or REJECT for each signal (e.g., "EXECUTE signal_1, REJECT signal_2")
2. Then provide detailed analysis:
   - Technical analysis alignment
   - Sentiment alignment
   - Risk assessment
   - Entry/exit levels
   - Stop loss recommendation
   - Take profit targets
   - Confidence score (0-100%)

Remember:
- Prioritize risk management above all
- Multiple confirming signals increase confidence
- Consider correlation between currency pairs
- Account for upcoming economic events
- Better to miss a trade than take a bad one
"""

class ForexStrategyEvaluator:
    def __init__(self, data_manager=None):
        """Initialize the Strategy Evaluator"""
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
        self.data_manager = data_manager
        self.backtest_engine = BacktestEngine(data_manager) if data_manager else None
        self.optimizer = StrategyOptimizer(self.backtest_engine) if self.backtest_engine else None
        self.simulator = MonteCarloSimulator(self.backtest_engine) if self.backtest_engine else None
        
    def evaluate_signals(self, pair, signals, technical_data, sentiment_data):
        """Evaluate trading signals using AI"""
        try:
            if not signals:
                return None
                
            # Format data for prompt
            signals_str = json.dumps(signals, indent=2)
            current_price = technical_data.get('current_price', 'N/A')
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": FOREX_EVAL_PROMPT.format(
                        strategy_signals=signals_str,
                        pair=pair,
                        current_price=current_price,
                        technical_data=json.dumps(technical_data, indent=2),
                        sentiment_data=json.dumps(sentiment_data, indent=2)
                    )
                }]
            )
            
            response = message.content
            
            # Parse response
            lines = response.split('\n')
            decisions = lines[0].strip().split(',')
            analysis = '\n'.join(lines[1:])
            
            # Extract recommendations
            recommendations = self._parse_recommendations(analysis)
            
            return {
                'decisions': decisions,
                'analysis': analysis,
                'recommendations': recommendations
            }
            
        except Exception as e:
            cprint(f"❌ Error evaluating signals: {str(e)}", "red")
            return None
            
    def _parse_recommendations(self, analysis):
        """Parse trading recommendations from AI analysis"""
        try:
            recommendations = {
                'entry_points': [],
                'exit_points': [],
                'stop_loss': None,
                'take_profit': None,
                'confidence': 0,
                'risk_rating': 'medium'
            }
            
            # Parse analysis text for specific recommendations
            lines = analysis.lower().split('\n')
            for line in lines:
                if 'stop loss' in line:
                    # Extract numeric values
                    import re
                    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                    if numbers:
                        recommendations['stop_loss'] = float(numbers[0])
                        
                if 'take profit' in line:
                    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                    if numbers:
                        recommendations['take_profit'] = float(numbers[0])
                        
                if 'confidence' in line:
                    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                    if numbers:
                        recommendations['confidence'] = float(numbers[0])
                        
                if 'risk' in line:
                    if 'high' in line:
                        recommendations['risk_rating'] = 'high'
                    elif 'low' in line:
                        recommendations['risk_rating'] = 'low'
                        
            return recommendations
            
        except Exception as e:
            cprint(f"❌ Error parsing recommendations: {str(e)}", "red")
            return None
            
    def print_backtest_results(self, backtest_results, chart=True, detailed=False):
        """
        Print backtest results for various strategies
        
        Args:
            backtest_results (dict): Dictionary containing backtest results for each strategy
                Format: {
                    'strategy_name': {
                        'trades': [{trade_details}],
                        'metrics': {
                            'profit_loss': float,
                            'win_rate': float,
                            'max_drawdown': float,
                            'sharpe_ratio': float,
                            'profit_factor': float,
                            'total_trades': int,
                            'winning_trades': int,
                            'losing_trades': int
                        }
                    }
                }
            chart (bool): Whether to display performance chart
            detailed (bool): Whether to show detailed trade information
        """
        try:
            if not backtest_results:
                cprint("❌ No backtest results to display", "red")
                return
                
            cprint("\n📊 BACKTEST RESULTS SUMMARY 📊", "cyan", attrs=["bold"])
            print("-" * 80)
            
            # Prepare summary table
            summary_data = []
            performance_data = {}
            
            for strategy_name, results in backtest_results.items():
                metrics = results.get('metrics', {})
                
                summary_data.append([
                    strategy_name,
                    f"{metrics.get('profit_loss', 0):.2f}",
                    f"{metrics.get('win_rate', 0) * 100:.1f}%",
                    f"{metrics.get('max_drawdown', 0):.2f}",
                    f"{metrics.get('sharpe_ratio', 0):.2f}",
                    metrics.get('total_trades', 0),
                    metrics.get('winning_trades', 0),
                    metrics.get('losing_trades', 0)
                ])
                
                # Store data for potential chart
                performance_data[strategy_name] = metrics.get('profit_loss', 0)
            
            # Print summary table
            headers = ["Strategy", "P/L", "Win Rate", "Max DD", "Sharpe", "Trades", "Wins", "Losses"]
            print(tabulate(summary_data, headers=headers, tablefmt="pretty"))
            print("-" * 80)
            
            # Use backtest engine for visualization if available
            if self.backtest_engine and chart:
                for strategy_name, results in backtest_results.items():
                    self.backtest_engine.results = results
                    self.backtest_engine.plot_equity_curve()
                    self.backtest_engine.plot_trade_distribution()
                    
                    # Run Monte Carlo simulation for robustness analysis
                    if self.simulator:
                        simulation_results = self.simulator.run_simulation(
                            results['strategy'],
                            results['symbol'],
                            results['start_date'],
                            results['end_date'],
                            results['timeframe'],
                            n_simulations=1000
                        )
                        self.simulator.plot_simulation_results()
            
            # Print detailed trade information if requested
            if detailed:
                for strategy_name, results in backtest_results.items():
                    trades = results.get('trades', [])
                    if trades:
                        cprint(f"\n🔍 Detailed Trades for {strategy_name} Strategy", "yellow")
                        
                        trade_data = []
                        for i, trade in enumerate(trades):
                            trade_data.append([
                                i + 1,
                                trade.get('pair', 'N/A'),
                                trade.get('direction', 'N/A'),
                                trade.get('entry_time', 'N/A'),
                                f"{trade.get('entry_price', 0):.5f}",
                                f"{trade.get('exit_price', 0):.5f}",
                                trade.get('exit_time', 'N/A'),
                                f"{trade.get('profit_loss', 0):.2f}",
                                trade.get('exit_reason', 'N/A')
                            ])
                        
                        trade_headers = ["#", "Pair", "Dir", "Entry Time", "Entry", "Exit", 
                                         "Exit Time", "P/L", "Exit Reason"]
                        print(tabulate(trade_data, headers=trade_headers, tablefmt="pretty"))
                        print("-" * 80)
            
            # Generate performance chart if requested and backtest engine not available
            if chart and not self.backtest_engine and performance_data:
                plt.figure(figsize=(10, 6))
                strategies = list(performance_data.keys())
                profits = list(performance_data.values())
                
                bar_colors = ['green' if p > 0 else 'red' for p in profits]
                plt.bar(strategies, profits, color=bar_colors)
                plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                
                plt.title('Strategy Performance Comparison')
                plt.xlabel('Strategy')
                plt.ylabel('Profit/Loss')
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                
                # Add profit/loss values on top of bars
                for i, v in enumerate(profits):
                    plt.text(i, v + (0.1 * (max(profits) if max(profits) > 0 else 1)), 
                             f"{v:.2f}", ha='center', fontsize=9)
                
                plt.tight_layout()
                plt.savefig(f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                cprint(f"✅ Performance chart saved", "green")
                plt.show()
            
        except Exception as e:
            cprint(f"❌ Error printing backtest results: {str(e)}", "red")