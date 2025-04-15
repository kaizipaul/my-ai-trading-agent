"""
Forex strategy manager
"""
from termcolor import cprint
from datetime import datetime
from src.utils.technical_analysis import TechnicalAnalysis
from src.agents.strategy_evaluator import ForexStrategyEvaluator

class ForexStrategyManager:
    def __init__(self, broker_client):
        """Initialize the Strategy Manager"""
        self.broker = broker_client
        self.evaluator = ForexStrategyEvaluator()
        self.technical_analyzer = TechnicalAnalysis()
        self.enabled_strategies = []
        
    def add_strategy(self, strategy):
        """Add a trading strategy"""
        self.enabled_strategies.append(strategy)
        cprint(f"✅ Added strategy: {strategy.name}", "green")
        
    def get_signals(self, pair):
        """Get signals from all enabled strategies"""
        try:
            signals = []
            cprint(f"\n🔍 Analyzing {pair} with {len(self.enabled_strategies)} strategies...", "cyan")
            
            # Get market data
            price_data = self.broker.get_price_data(pair)
            technical_data = self.technical_analyzer.calculate_indicators(price_data)
            sentiment_data = self.broker.get_sentiment_data(pair)
            
            # Collect signals from all strategies
            for strategy in self.enabled_strategies:
                signal = strategy.generate_signals(pair, technical_data)
                if signal:
                    signals.append({
                        'pair': pair,
                        'strategy_name': strategy.name,
                        'signal': signal['signal'],
                        'direction': signal['direction'],
                        'strength': signal['strength'],
                        'metadata': signal.get('metadata', {})
                    })
            
            if not signals:
                cprint(f"ℹ️ No strategy signals for {pair}", "yellow")
                return []
                
            # Evaluate signals
            evaluation = self.evaluator.evaluate_signals(
                pair,
                signals,
                technical_data.to_dict(),
                sentiment_data
            )
            
            if not evaluation:
                return []
                
            # Filter approved signals
            approved_signals = []
            for signal, decision in zip(signals, evaluation['decisions']):
                if "EXECUTE" in decision.upper():
                    signal['recommendations'] = evaluation['recommendations']
                    approved_signals.append(signal)
                    cprint(f"✅ Approved: {signal['strategy_name']} {signal['direction']}", "green")
                else:
                    cprint(f"❌ Rejected: {signal['strategy_name']} {signal['direction']}", "red")
                    
            return approved_signals
            
        except Exception as e:
            cprint(f"❌ Error getting strategy signals: {str(e)}", "red")
            return []
            
    def execute_signals(self, approved_signals):
        """Execute approved trading signals"""
        try:
            if not approved_signals:
                return
                
            cprint("\n🚀 Executing approved signals...", "cyan")
            
            for signal in approved_signals:
                try:
                    pair = signal['pair']
                    direction = signal['direction']
                    recommendations = signal['recommendations']
                    
                    if direction == 'BUY':
                        self.broker.create_order(
                            pair=pair,
                            order_type='MARKET',
                            side='BUY',
                            stop_loss=recommendations['stop_loss'],
                            take_profit=recommendations['take_profit']
                        )
                        cprint(f"✅ Executed BUY for {pair}", "green")
                        
                    elif direction == 'SELL':
                        self.broker.create_order(
                            pair=pair,
                            order_type='MARKET',
                            side='SELL',
                            stop_loss=recommendations['stop_loss'],
                            take_profit=recommendations['take_profit']
                        )
                        cprint(f"✅ Executed SELL for {pair}", "green")
                        
                except Exception as e:
                    cprint(f"❌ Error executing signal: {str(e)}", "red")
                    continue
                    
        except Exception as e:
            cprint(f"❌ Error executing signals: {str(e)}", "red")