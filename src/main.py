"""
Trading Analysis & Position Recommendation System
Main entry point for running trading analysis agents and backtesting
"""

import os
import sys
from termcolor import cprint, colored
from dotenv import load_dotenv
import time
import pandas as pd
from datetime import datetime, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import configuration
from src.config import *

# Import agents
from src.agents.trading_agent import ForexTradingAgent
from src.agents.risk_agent import ForexRiskAgent
from src.agents.technical_agent import TechnicalAgent
from src.agents.news_sentiment_agent import NewsSentimentAgent

# Import backtesting
from src.backtesting import BacktestEngine, StrategyOptimizer, MonteCarloSimulator
from src.data.historical_data_manager import HistoricalDataManager

# Import strategies
from src.strategies import (
    RSIDivergenceStrategy,
    BreakoutDetectionStrategy,
    PatternRecognitionStrategy,
    KishokaStrategy,
    MovingAverageStrategy
)

# Load environment variables
load_dotenv()

# Agent Configuration
ACTIVE_AGENTS = {
    'risk': True,      # Risk management agent
    'trading': True,   # Main trading agent
    'technical': True, # Technical analysis agent
    'sentiment': False, # News sentiment agent (set to False to run faster)
}

def run_agents(selected_symbols=None, single_run=False):
    """Run all active agents in sequence"""
    try:
        # Use all symbols if none selected
        if not selected_symbols:
            selected_symbols = FOREX_PAIRS
        
        # Initialize active agents
        trading_agent = ForexTradingAgent() if ACTIVE_AGENTS['trading'] else None
        risk_agent = ForexRiskAgent() if ACTIVE_AGENTS['risk'] else None
        technical_agent = TechnicalAgent() if ACTIVE_AGENTS['technical'] else None
        sentiment_agent = NewsSentimentAgent() if ACTIVE_AGENTS['sentiment'] else None

        while True:
            try:
                # Run Risk Management
                if risk_agent:
                    cprint("\n🛡️ Running Risk Management...", "cyan")
                    risk_agent.run()

                # Run Trading Analysis - pass selected_symbols to agent
                if trading_agent:
                    cprint("\n🤖 Running Trading Analysis...", "cyan")
                    # Don't use the built-in run() method which loops over all pairs
                    for pair in selected_symbols:
                        cprint(f"\n📊 Analyzing {pair}...", "cyan")
                        trading_agent.analyze_pair(pair)
                    # Display summary of recommendations
                    trading_agent.display_all_recommendations()
                    
                    # Display current positions if trade execution is enabled
                    if EXECUTE_TRADES:
                        trading_agent.display_current_positions()

                # Run Technical Analysis
                if technical_agent:
                    cprint("\n📊 Running Technical Analysis...", "cyan")
                    for pair in selected_symbols:
                        cprint(f"\n🔍 Analyzing {pair}...", "cyan")
                        technical_agent.analyze_pair(pair)

                # Run Sentiment Analysis - pass selected_symbols to agent
                if sentiment_agent:
                    cprint("\n🎭 Running News Sentiment Analysis...", "cyan")
                    # Don't use the built-in run() method which loops over all pairs
                    for pair in selected_symbols:
                        sentiment = sentiment_agent.analyze_pair_sentiment(pair)
                        sentiment_agent.sentiment_scores[pair] = sentiment
                        sentiment_agent.announce_significant_sentiment(pair, sentiment)

                # If single run mode, exit after one cycle
                if single_run:
                    cprint("\n✅ Single run completed!", "green")
                    break

                # Sleep until next cycle
                next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
                cprint(f"\n😴 Sleeping until {next_run.strftime('%H:%M:%S')}", "cyan")
                time.sleep(60 * SLEEP_BETWEEN_RUNS_MINUTES)

            except Exception as e:
                cprint(f"\n❌ Error running agents: {str(e)}", "red")
                cprint("🔄 Continuing to next cycle...", "yellow")
                time.sleep(60)
                if single_run:
                    break

    except KeyboardInterrupt:
        cprint("\n👋 Gracefully shutting down...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error in main loop: {str(e)}", "red")
        raise

def run_backtesting(strategy, symbol, start_date=None, end_date=None, timeframe='1d', show_charts=True):
    """Run backtesting for a specified strategy and symbol"""
    try:
        cprint(f"\n📊 Running backtest for {strategy.name} on {symbol}...", "cyan")
        
        # Set default dates if not specified
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # Initialize data manager and backtest engine
        data_manager = HistoricalDataManager()
        backtest_engine = BacktestEngine(data_manager)
        
        # Run backtest
        results = backtest_engine.run_backtest(
            strategy=strategy,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )
        
        # Display results
        cprint("\n✅ Backtest completed!", "green")
        cprint("\n📈 Performance Summary:", "cyan")
        metrics = results['metrics']
        
        # Print summary
        summary_table = [
            ["Initial Capital", f"${results['initial_capital']:,.2f}"],
            ["Final Capital", f"${results['final_capital']:,.2f}"],
            ["Total Return", f"{results['total_return']*100:.2f}%"],
            ["Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}"],
            ["Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%"],
            ["Win Rate", f"{metrics['win_rate']*100:.2f}%"],
            ["Profit Factor", f"{metrics['profit_factor']:.2f}"],
            ["Number of Trades", f"{len([t for t in results['trades'] if t['type'] == 'sell'])}"]
        ]
        
        # Print table
        for row in summary_table:
            print(f"{colored(row[0], 'yellow'):20} {row[1]}")
            
        # Show charts if requested
        if show_charts:
            backtest_engine.plot_equity_curve()
            backtest_engine.plot_trade_distribution()
            
        return results
        
    except Exception as e:
        cprint(f"\n❌ Error running backtest: {str(e)}", "red")
        return None

def select_strategy():
    """Menu to select a trading strategy"""
    strategies = {
        1: {"name": "RSI Divergence", "class": RSIDivergenceStrategy},
        2: {"name": "Breakout Detection", "class": BreakoutDetectionStrategy},
        3: {"name": "Pattern Recognition", "class": PatternRecognitionStrategy},
        4: {"name": "Kishoka", "class": KishokaStrategy},
        5: {"name": "Moving Average", "class": MovingAverageStrategy}
    }
    
    while True:
        print("\n" + "=" * 50)
        cprint("📈 Select a Trading Strategy", "cyan")
        print("=" * 50)
        
        for key, strategy in strategies.items():
            print(f"{key}. {strategy['name']}")
        print("0. Back to Main Menu")
        
        try:
            choice = int(input("\nEnter your choice (0-5): "))
            if choice == 0:
                return None
            elif choice in strategies:
                return strategies[choice]["class"](name=strategies[choice]["name"])
            else:
                cprint("Invalid choice. Please try again.", "red")
        except ValueError:
            cprint("Please enter a number.", "red")

def select_symbol(all_option=True):
    """Menu to select a trading symbol"""
    # Create a dictionary of available symbols with index
    symbols = {i+1: symbol for i, symbol in enumerate(FOREX_PAIRS)}
    
    while True:
        print("\n" + "=" * 50)
        cprint("🌐 Select a Trading Symbol", "cyan")
        print("=" * 50)
        
        # Display symbols grouped by type
        cprint("\nForex Pairs:", "yellow")
        forex_pairs = [s for s in FOREX_PAIRS if is_forex_pair(s)]
        for i, symbol in enumerate(forex_pairs):
            idx = list(FOREX_PAIRS).index(symbol) + 1
            print(f"{idx}. {symbol}")
            
        cprint("\nStocks:", "yellow")
        stocks = [s for s in FOREX_PAIRS if not is_forex_pair(s)]
        for i, symbol in enumerate(stocks):
            idx = list(FOREX_PAIRS).index(symbol) + 1
            print(f"{idx}. {symbol}")
        
        if all_option:
            print("\n0. All Symbols")
        print("00. Back to Main Menu")
        
        try:
            choice = input("\nEnter your choice: ")
            if choice == "00":
                return None
            
            choice = int(choice)
            if choice == 0 and all_option:
                return FOREX_PAIRS
            elif choice in symbols:
                return [symbols[choice]]
            else:
                cprint("Invalid choice. Please try again.", "red")
        except ValueError:
            cprint("Please enter a number.", "red")

def alpaca_trading_menu():
    """Menu for Alpaca trading operations"""
    global EXECUTE_TRADES
    trading_agent = ForexTradingAgent()
    
    while True:
        print("\n" + "=" * 50)
        cprint("🤖 Alpaca Trading Menu", "cyan")
        print("=" * 50)
        
        # Display trade execution status
        status_color = "green" if EXECUTE_TRADES else "red"
        status_text = "ENABLED" if EXECUTE_TRADES else "DISABLED"
        cprint(f"Trade Execution Status: {status_text}", status_color)
        
        # Display menu options
        print("\n1. View Current Positions")
        print("2. Close a Position")
        print("3. Close All Positions")
        print("4. Toggle Trade Execution")
        print("5. Run Analysis with Current Settings")
        print("0. Back to Main Menu")
        
        try:
            choice = int(input("\nEnter your choice (0-5): "))
            
            if choice == 0:
                break
            elif choice == 1:
                # View positions
                trading_agent.display_current_positions()
            elif choice == 2:
                # Close a specific position
                positions = trading_agent.position_manager.get_positions()
                
                if not positions:
                    cprint("No open positions to close.", "yellow")
                    continue
                
                # Display positions
                cprint("\nOpen Positions:", "cyan")
                for i, pos in enumerate(positions):
                    print(f"{i+1}. {pos['pair']}: {pos['direction'].upper()} {pos['size']} @ {pos['entry_price']}")
                
                try:
                    pos_choice = int(input("\nEnter position number to close (0 to cancel): "))
                    if pos_choice == 0:
                        continue
                    if 1 <= pos_choice <= len(positions):
                        symbol = positions[pos_choice-1]['pair']
                        if trading_agent.close_position(symbol):
                            cprint(f"Position {symbol} closed successfully.", "green")
                        else:
                            cprint(f"Failed to close position {symbol}.", "red")
                    else:
                        cprint("Invalid position number.", "red")
                except ValueError:
                    cprint("Please enter a valid number.", "red")
            elif choice == 3:
                # Close all positions
                confirm = input("Are you sure you want to close all positions? (y/n): ")
                if confirm.lower() == 'y':
                    if trading_agent.close_all_positions():
                        cprint("All positions closed successfully.", "green")
                    else:
                        cprint("Failed to close all positions.", "red")
            elif choice == 4:
                # Toggle trade execution
                current = "enabled" if EXECUTE_TRADES else "disabled"
                new = "disable" if EXECUTE_TRADES else "enable"
                
                confirm = input(f"Trade execution is currently {current}. Are you sure you want to {new} it? (y/n): ")
                if confirm.lower() == 'y':
                    EXECUTE_TRADES = not EXECUTE_TRADES
                    
                    # Set environment variable
                    os.environ['EXECUTE_TRADES'] = 'true' if EXECUTE_TRADES else 'false'
                    
                    new_status = "ENABLED" if EXECUTE_TRADES else "DISABLED"
                    cprint(f"Trade execution is now {new_status}.", "green")
            elif choice == 5:
                # Run analysis with current settings
                symbols = select_symbol()
                if symbols:
                    run_agents(symbols, True)
            else:
                cprint("Invalid choice. Please try again.", "red")
        except ValueError:
            cprint("Please enter a number.", "red")
        except Exception as e:
            cprint(f"Error: {str(e)}", "red")

def backtesting_menu():
    """Backtesting menu system"""
    while True:
        print("\n" + "=" * 50)
        cprint("📊 Backtesting Menu", "cyan")
        print("=" * 50)
        
        print("1. Run Backtest")
        print("2. Strategy Optimization")
        print("3. Monte Carlo Simulation")
        print("0. Back to Main Menu")
        
        try:
            choice = int(input("\nEnter your choice (0-3): "))
            
            if choice == 0:
                break
            elif choice == 1:
                # Run a backtest
                strategy = select_strategy()
                if not strategy:
                    continue
                    
                symbols = select_symbol(all_option=False)
                if not symbols:
                    continue
                    
                # Get dates from user
                default_start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                start_date = input(f"Enter start date (YYYY-MM-DD) [default: {default_start}]: ")
                if not start_date:
                    start_date = default_start
                    
                default_end = datetime.now().strftime('%Y-%m-%d')
                end_date = input(f"Enter end date (YYYY-MM-DD) [default: {default_end}]: ")
                if not end_date:
                    end_date = default_end
                    
                # Get timeframe
                timeframe_options = {
                    '1': '1d',
                    '2': '4h',
                    '3': '1h',
                    '4': '15m'
                }
                print("\nSelect timeframe:")
                for key, tf in timeframe_options.items():
                    print(f"{key}. {tf}")
                    
                tf_choice = input("\nEnter timeframe choice [default: 1]: ")
                if not tf_choice or tf_choice not in timeframe_options:
                    tf_choice = '1'
                    
                timeframe = timeframe_options[tf_choice]
                
                # Run the backtest
                run_backtesting(
                    strategy=strategy,
                    symbol=symbols[0],
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe,
                    show_charts=True
                )
                
            elif choice == 2:
                # Strategy optimization
                cprint("\nStrategy Optimization", "cyan")
                
                strategy = select_strategy()
                if not strategy:
                    continue
                    
                symbols = select_symbol(all_option=False)
                if not symbols:
                    continue
                    
                # Create optimizer
                data_manager = HistoricalDataManager()
                optimizer = StrategyOptimizer(data_manager)
                
                cprint("\nRunning optimization...", "cyan")
                results = optimizer.optimize_strategy(
                    strategy=strategy,
                    symbol=symbols[0],
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d')
                )
                
                cprint("\nOptimization Results:", "green")
                optimizer.display_results()
                
            elif choice == 3:
                # Monte Carlo simulation
                cprint("\nMonte Carlo Simulation", "cyan")
                
                strategy = select_strategy()
                if not strategy:
                    continue
                    
                symbols = select_symbol(all_option=False)
                if not symbols:
                    continue
                    
                # Create simulator
                data_manager = HistoricalDataManager()
                simulator = MonteCarloSimulator(data_manager)
                
                cprint("\nRunning Monte Carlo simulation...", "cyan")
                simulator.run_simulation(
                    strategy=strategy,
                    symbol=symbols[0],
                    simulations=100,
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d')
                )
                
                cprint("\nMonte Carlo Results:", "green")
                simulator.display_results()
            else:
                cprint("Invalid choice. Please try again.", "red")
        except ValueError:
            cprint("Please enter a number.", "red")
        except Exception as e:
            cprint(f"Error: {str(e)}", "red")

def main_menu():
    """Main menu system"""
    # Print welcome message
    print("\n" + "=" * 80)
    cprint("Welcome to Forex & Stock Trading Analysis System", "cyan", attrs=["bold"])
    print("=" * 80)
    cprint("This system analyzes financial markets and provides trading recommendations.", "white")
    
    if EXECUTE_TRADES:
        cprint("⚠️ LIVE TRADING IS ENABLED - The system will automatically execute trades via Alpaca!", "white", "on_red")
    
    while True:
        print("\n" + "=" * 50)
        cprint("Main Menu", "cyan")
        print("=" * 50)
        
        print("1. Run Analysis on Single Symbol")
        print("2. Run Analysis on All Symbols")
        print("3. Backtesting Tools")
        print("4. Alpaca Trading Menu")
        print("0. Exit")
        
        try:
            choice = int(input("\nEnter your choice (0-4): "))
            
            if choice == 0:
                cprint("\nExiting...", "yellow")
                break
            elif choice == 1:
                # Run analysis on a single symbol
                symbols = select_symbol(all_option=False)
                if symbols:
                    run_agents(symbols, True)
            elif choice == 2:
                # Run analysis on all symbols
                run_agents(FOREX_PAIRS, True)
            elif choice == 3:
                # Backtesting tools
                backtesting_menu()
            elif choice == 4:
                # Alpaca trading menu
                alpaca_trading_menu()
            else:
                cprint("Invalid choice. Please try again.", "red")
        except ValueError:
            cprint("Please enter a number.", "red")
        except Exception as e:
            cprint(f"Error: {str(e)}", "red")
            
    print("\nThank you for using the Trading Analysis System. Goodbye!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line arguments for automation
        if sys.argv[1] == "--run-all":
            run_agents(FOREX_PAIRS, True)
        elif sys.argv[1] == "--run" and len(sys.argv) > 2:
            symbol = sys.argv[2]
            if symbol in FOREX_PAIRS:
                run_agents([symbol], True)
            else:
                cprint(f"Symbol {symbol} not found in configuration", "red")
    else:
        # Interactive mode
        main_menu()