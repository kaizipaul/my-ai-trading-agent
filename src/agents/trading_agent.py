"""
Main trading agent responsible for coordinating trading analysis and position recommendations
"""
from datetime import datetime
import pandas as pd
from termcolor import cprint
from src.config import FOREX_PAIRS, TIMEFRAMES, STRATEGY_MIN_CONFIDENCE, EXECUTE_TRADES
from src.utils.yfinance_data_fetcher import YFinanceDataFetcher
from src.utils.technical_analysis import TechnicalAnalysis
from src.utils.position_recommender import PositionRecommender
from src.strategies.moving_average_strategy import MovingAverageStrategy
from src.strategies.kishoka_strategy import KishokaStrategy
from src.utils.alpaca_order_executor import AlpacaOrderExecutor
from src.utils.alpaca_position_manager import AlpacaPositionManager

class ForexTradingAgent:
    def __init__(self):
        self.data_fetcher = YFinanceDataFetcher()
        self.position_recommender = PositionRecommender()
        self.strategies = {
            'moving_average': MovingAverageStrategy(),
            'kishoka_killswitch': KishokaStrategy()
        }
        self.recommendations = {}  # Store latest recommendations
        
        # Initialize Alpaca components for trade execution
        self.order_executor = AlpacaOrderExecutor()
        self.position_manager = AlpacaPositionManager()
        
    def run(self):
        """Main analysis cycle"""
        for pair in FOREX_PAIRS:
            cprint(f"\n📊 Analyzing {pair}...", "cyan")
            self.analyze_pair(pair)
            
        # After analysis, display all recommendations
        self.display_all_recommendations()
        
        # Display current positions from Alpaca if trade execution is enabled
        if EXECUTE_TRADES:
            self.display_current_positions()
            
    def analyze_pair(self, pair):
        """Analyze a specific trading instrument for opportunities"""
        try:
            # Get market data for multiple timeframes
            data = {}
            for timeframe in TIMEFRAMES:
                data[timeframe] = self.get_market_data(pair, timeframe)
                
            # Generate trading signals
            signals = self.generate_signals(pair, data)
            
            # Generate position recommendation
            if signals and signals.get('confidence', 0) > 0:
                recommendation = self.generate_recommendation(pair, signals, data[signals.get('timeframe', TIMEFRAMES[0])])
                
                # Execute trade if enabled in config
                if EXECUTE_TRADES and recommendation["recommendation"] != "NEUTRAL":
                    self.execute_recommendation(recommendation)
            else:
                cprint(f"⏳ No clear opportunity for {pair} at this time", "yellow")
                
        except Exception as e:
            cprint(f"❌ Error analyzing {pair}: {str(e)}", "red")
            
    def get_market_data(self, pair, timeframe='1h', count=100):
        """Fetch market data for analysis"""
        cprint(f"📈 Fetching {timeframe} data for {pair}...", "blue")
        df = self.data_fetcher.get_price_data(pair, timeframe, count)
        
        if df is not None and not df.empty:
            # Add technical indicators
            df = TechnicalAnalysis.add_all_indicators(df)
            return df
        
        return None
        
    def generate_signals(self, pair, data):
        """Generate trading signals based on market data"""
        if not data or all(df is None for df in data.values()):
            cprint(f"⚠️ No data available for {pair}", "yellow")
            return None
            
        # Combine signals from different strategies
        combined_signals = {
            'direction': None,
            'confidence': 0,
            'entry_price': None,
            'stop_loss': None,
            'take_profit': None,
            'timeframe': None,
            'strategy': None
        }
        
        # Process each strategy
        for strategy_name, strategy in self.strategies.items():
            for timeframe, df in data.items():
                if df is not None and not df.empty:
                    signal = strategy.generate_signal(pair, df)
                    
                    if signal and signal.get('confidence', 0) > combined_signals['confidence']:
                        combined_signals = signal
                        combined_signals['timeframe'] = timeframe
                        combined_signals['strategy'] = strategy_name
        
        # Only recommend if confidence exceeds minimum threshold
        if combined_signals['confidence'] >= STRATEGY_MIN_CONFIDENCE:
            # Get current price if not provided
            if not combined_signals['entry_price']:
                combined_signals['entry_price'] = self.data_fetcher.get_current_price(pair)
                
            cprint(f"🎯 {combined_signals['strategy'].upper()} signal generated for {pair}", "green")
            cprint(f"    Direction: {combined_signals['direction'].upper()}", "green")
            cprint(f"    Confidence: {combined_signals['confidence']:.2f}", "green")
            cprint(f"    Entry: {combined_signals['entry_price']}", "green")
            cprint(f"    Stop Loss: {combined_signals['stop_loss']}", "green")
            cprint(f"    Take Profit: {combined_signals['take_profit']}", "green")
            
        return combined_signals
        
    def generate_recommendation(self, pair, signals, price_data):
        """Generate a position recommendation based on signals"""
        # Convert signal direction to recommendation type
        rec_type = "NEUTRAL"
        if signals['direction'] == 'buy':
            rec_type = "LONG"
        elif signals['direction'] == 'sell':
            rec_type = "SHORT"
            
        # Use the PositionRecommender to refine the recommendation
        technical_indicators = self._extract_indicators(price_data)
        
        # Create a basic recommendation from the signals
        basic_recommendation = {
            "symbol": pair,
            "recommendation": rec_type,
            "confidence": signals['confidence'],
            "entry_price": signals['entry_price'],
            "stop_loss": signals['stop_loss'],
            "take_profit": signals['take_profit'],
            "timestamp": datetime.now().isoformat(),
            "timeframe": signals['timeframe'],
            "strategy": signals['strategy']
        }
        
        # Get a more detailed recommendation from the position recommender
        detailed_recommendation = self.position_recommender.analyze_and_recommend(
            pair, price_data, technical_indicators
        )
        
        # Merge recommendations, preferring the detailed one if available
        # but keeping original signal info for context
        final_recommendation = {**basic_recommendation, **detailed_recommendation}
        final_recommendation['strategy_signals'] = signals
        
        # Calculate position size based on risk management
        if 'entry_price' in final_recommendation and 'stop_loss' in final_recommendation:
            position_size = self.position_manager.calculate_position_size(
                pair,
                float(final_recommendation['entry_price']),
                float(final_recommendation['stop_loss'])
            )
            final_recommendation['position_size'] = position_size
        
        # Store the recommendation
        self.recommendations[pair] = final_recommendation
        
        # Display the recommendation
        self._display_recommendation(final_recommendation)
        
        return final_recommendation
        
    def _extract_indicators(self, price_data):
        """Extract technical indicators from price data for the recommendation engine"""
        indicators = {}
        
        # Extract key indicators if available
        for indicator in ['rsi', 'macd', 'macd_signal', 'atr', 'sma_50', 'ema_200']:
            if indicator in price_data.columns:
                indicators[indicator] = price_data[indicator].iloc[-1]
                
        return indicators
        
    def _display_recommendation(self, recommendation):
        """Display a formatted position recommendation"""
        output_lines, color = self.position_recommender.format_recommendation_output(recommendation)
        
        # Print recommendation with color
        for line in output_lines:
            cprint(line, color)
            
        # Add optional additional information
        if 'strategy' in recommendation and 'timeframe' in recommendation:
            cprint(f"📈 Based on {recommendation['strategy'].upper()} strategy ({recommendation['timeframe']})", color)
            
        print("\n")  # Add space after recommendation
        
    def display_all_recommendations(self):
        """Display a summary of all position recommendations"""
        if not self.recommendations:
            cprint("❌ No position recommendations available", "red")
            return
            
        cprint("\n=== 📝 POSITION RECOMMENDATIONS SUMMARY ===", "white", "on_blue")
        
        for pair, rec in self.recommendations.items():
            direction = rec["recommendation"]
            confidence = rec["confidence"]
            entry = rec["entry_price"]
            sl = rec["stop_loss"]
            tp = rec["take_profit"]
            
            # Choose color based on recommendation
            color = "yellow"
            if direction == "LONG":
                color = "green"
            elif direction == "SHORT":
                color = "red"
                
            size_text = f"Size: {rec.get('position_size', 'N/A')}" if 'position_size' in rec else ""
            cprint(f"{pair}: {direction} @ {entry} (SL: {sl}, TP: {tp}) {size_text} - Confidence: {confidence:.2f}", color)
            
        if EXECUTE_TRADES:
            cprint("\n🤖 Auto-execution is ENABLED. Recommendations will be automatically executed.", "white", "on_green")
        else:
            cprint("\n💡 Copy and paste the recommendation details to your trading platform", "white")
            cprint("📊 Full analysis details are provided above for each instrument", "white")
        
        cprint("====================================================", "white", "on_blue")
        
    def execute_recommendation(self, recommendation):
        """Execute a trade based on a recommendation using Alpaca Markets"""
        symbol = recommendation['symbol']
        direction = recommendation['recommendation'].lower()
        entry_price = float(recommendation['entry_price'])
        stop_loss = float(recommendation['stop_loss']) if recommendation['stop_loss'] else None
        take_profit = float(recommendation['take_profit']) if recommendation['take_profit'] else None
        position_size = float(recommendation.get('position_size', 0))
        
        if direction == "neutral" or position_size <= 0:
            cprint(f"⏹️ No trade execution needed for {symbol} (Neutral recommendation or zero position size)", "yellow")
            return False
            
        # Check if we already have a position for this symbol
        current_positions = self.position_manager.get_positions()
        existing_position = next((p for p in current_positions if p['pair'] == symbol), None)
        
        if existing_position:
            # If direction matches, we might increase position or do nothing
            existing_direction = 'long' if existing_position['direction'] == 'buy' else 'short'
            
            if (existing_direction == direction.lower() or 
                (existing_direction == 'long' and direction.lower() == 'buy') or 
                (existing_direction == 'short' and direction.lower() == 'sell')):
                
                cprint(f"⏩ Already have a {direction} position for {symbol}, skipping execution", "yellow")
                return False
            else:
                # Close existing position as we're going the opposite direction
                cprint(f"🔄 Closing existing {existing_direction} position for {symbol} to reverse direction", "yellow")
                self.order_executor.close_trade(symbol)
                self.position_manager.close_position(symbol, exit_price=entry_price, reason="direction_change")
        
        # Convert direction for Alpaca ("LONG"/"SHORT" to "buy"/"sell")
        alpaca_direction = "buy" if direction.lower() in ["long", "buy"] else "sell"
        
        # Place the order
        cprint(f"🚀 Executing {direction} trade for {symbol} @ {entry_price}", "cyan")
        
        order_result = self.order_executor.place_market_order(
            symbol, 
            alpaca_direction, 
            position_size, 
            stop_loss, 
            take_profit
        )
        
        if order_result:
            # Record the position in our position manager for tracking
            self.position_manager.open_position(
                symbol,
                alpaca_direction,
                entry_price,
                position_size,
                stop_loss,
                take_profit
            )
            
            cprint(f"✅ Order executed successfully for {symbol}", "green")
            return True
        else:
            cprint(f"❌ Failed to execute order for {symbol}", "red")
            return False
            
    def display_current_positions(self):
        """Display current positions from Alpaca"""
        positions = self.position_manager.get_positions()
        
        if not positions:
            cprint("\n🔍 No current positions open", "yellow")
            return
            
        cprint("\n=== 📊 CURRENT POSITIONS ===", "white", "on_blue")
        
        for pos in positions:
            direction = pos['direction'].upper()
            entry_price = pos['entry_price']
            current_price = pos['current_price']
            size = pos['size']
            unrealized_pl = pos['unrealized_pl']
            
            # Choose color based on P/L
            color = "green" if float(unrealized_pl) >= 0 else "red"
            
            cprint(f"{pos['pair']}: {direction} {size} @ {entry_price} (Current: {current_price}, P/L: {float(unrealized_pl):.2f})", color)
            
        cprint("============================", "white", "on_blue")
    
    def close_position(self, symbol):
        """Close a specific position"""
        result = self.order_executor.close_trade(symbol)
        
        if result:
            self.position_manager.close_position(symbol, reason="manual_close")
            cprint(f"✅ Closed position for {symbol}", "green")
            return True
        else:
            cprint(f"❌ Failed to close position for {symbol}", "red")
            return False
        
    def close_all_positions(self):
        """Close all open positions"""
        result = self.order_executor.close_all_positions()
        
        if result:
            # Close all positions in our records
            positions = self.position_manager.get_positions()
            for pos in positions:
                self.position_manager.close_position(pos['pair'], reason="close_all")
                
            cprint("✅ Closed all positions", "green")
            return True
        else:
            cprint("❌ Failed to close all positions", "red")
            return False