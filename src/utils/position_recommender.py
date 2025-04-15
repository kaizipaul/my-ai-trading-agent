"""
Position recommendation utility for analyzing market data and providing trading recommendations
"""
import pandas as pd
import numpy as np
from datetime import datetime
from termcolor import cprint

class PositionRecommender:
    """
    Analyzes market data and provides position recommendations
    without actually executing trades.
    """
    
    def __init__(self):
        """Initialize the position recommender"""
        pass
        
    def analyze_and_recommend(self, symbol, price_data, technical_indicators=None, sentiment_score=None):
        """
        Analyze the price data and provide a position recommendation
        
        Args:
            symbol (str): The trading symbol
            price_data (pd.DataFrame): Historical price data
            technical_indicators (dict, optional): Dictionary of technical indicators
            sentiment_score (float, optional): News sentiment score from -1.0 to 1.0
            
        Returns:
            dict: Position recommendation details
        """
        if price_data is None or len(price_data) < 10:
            cprint(f"❌ Insufficient data for {symbol} to make a recommendation", "red")
            return {
                "symbol": symbol,
                "recommendation": "NEUTRAL",
                "confidence": 0.0,
                "entry_price": None,
                "take_profit": None,
                "stop_loss": None,
                "risk_reward_ratio": None,
                "timestamp": datetime.now().isoformat(),
                "reason": "Insufficient data"
            }
            
        # Calculate basic signals
        signals = {}
        
        # 1. Moving Average signals
        signals.update(self._calculate_ma_signals(price_data))
        
        # 2. RSI signals
        signals.update(self._calculate_rsi_signals(price_data))
        
        # 3. MACD signals
        signals.update(self._calculate_macd_signals(price_data))
        
        # 4. Price action signals
        signals.update(self._calculate_price_action_signals(price_data))
        
        # 5. Volatility based signals
        signals.update(self._calculate_volatility_signals(price_data))
        
        # 6. Include technical indicators if provided
        if technical_indicators:
            for indicator, value in technical_indicators.items():
                signals[indicator] = value
                
        # 7. Include sentiment score if provided
        sentiment_signal = 0
        if sentiment_score is not None:
            # Convert -1.0 to 1.0 sentiment to a signal
            sentiment_signal = sentiment_score
            signals["sentiment"] = sentiment_signal
            
        # Aggregate signals and determine overall recommendation
        long_signals = sum(1 for value in signals.values() if value > 0)
        short_signals = sum(1 for value in signals.values() if value < 0)
        neutral_signals = sum(1 for value in signals.values() if value == 0)
        
        total_signals = long_signals + short_signals + neutral_signals
        if total_signals == 0:
            total_signals = 1  # Avoid division by zero
            
        # Calculate net signal and confidence
        net_signal = (long_signals - short_signals) / total_signals
        
        # Determine recommendation
        recommendation = "NEUTRAL"
        if net_signal > 0.3:
            recommendation = "LONG"
        elif net_signal < -0.3:
            recommendation = "SHORT"
            
        # Calculate confidence
        confidence = abs(net_signal)
        
        # Get current price
        current_price = float(price_data['close'].iloc[-1])
        
        # Calculate volatility (using ATR-like approach)
        highs = price_data['high'].values
        lows = price_data['low'].values
        closes = price_data['close'].values
        
        ranges = []
        for i in range(1, len(closes)):
            true_range = max(
                highs[i] - lows[i],                  # Current high - low
                abs(highs[i] - closes[i-1]),         # Current high - previous close
                abs(lows[i] - closes[i-1])           # Current low - previous close
            )
            ranges.append(true_range)
            
        avg_range = np.mean(ranges[-14:]) if ranges else current_price * 0.01
        
        # Determine stop loss and take profit based on volatility
        stop_loss_pips = avg_range * 2
        take_profit_pips = avg_range * 3
        
        if recommendation == "LONG":
            entry_price = current_price
            stop_loss = entry_price - stop_loss_pips
            take_profit = entry_price + take_profit_pips
        elif recommendation == "SHORT":
            entry_price = current_price
            stop_loss = entry_price + stop_loss_pips
            take_profit = entry_price - take_profit_pips
        else:
            entry_price = current_price
            stop_loss = None
            take_profit = None
            
        # Calculate risk/reward ratio
        risk_reward_ratio = None
        if recommendation != "NEUTRAL" and stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(entry_price - take_profit)
            if risk > 0:
                risk_reward_ratio = round(reward / risk, 2)
                
        # Format reasons
        reasons = []
        for signal, value in signals.items():
            if value > 0:
                reasons.append(f"{signal}: Bullish")
            elif value < 0:
                reasons.append(f"{signal}: Bearish")
                
        # Create recommendation object
        position_recommendation = {
            "symbol": symbol,
            "recommendation": recommendation,
            "confidence": round(confidence, 2),
            "entry_price": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5) if stop_loss else None,
            "take_profit": round(take_profit, 5) if take_profit else None,
            "risk_reward_ratio": risk_reward_ratio,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "signals": signals,
                "reasons": reasons
            }
        }
        
        return position_recommendation
        
    def _calculate_ma_signals(self, price_data):
        """Calculate Moving Average based signals"""
        signals = {}
        
        # Calculate short-term MA (10 periods)
        price_data['ma_short'] = price_data['close'].rolling(window=10).mean()
        
        # Calculate mid-term MA (50 periods)
        price_data['ma_mid'] = price_data['close'].rolling(window=50).mean()
        
        # Calculate long-term MA (200 periods or max available)
        ma_long_window = min(200, len(price_data) // 2)
        price_data['ma_long'] = price_data['close'].rolling(window=ma_long_window).mean()
        
        # Skip if not enough data
        if price_data['ma_short'].isna().iloc[-1] or price_data['ma_mid'].isna().iloc[-1]:
            return signals
            
        # Signal 1: Short MA vs Mid MA
        last_close = price_data['close'].iloc[-1]
        last_ma_short = price_data['ma_short'].iloc[-1]
        last_ma_mid = price_data['ma_mid'].iloc[-1]
        
        if last_ma_short > last_ma_mid:
            signals['ma_cross'] = 1  # Bullish
        elif last_ma_short < last_ma_mid:
            signals['ma_cross'] = -1  # Bearish
        else:
            signals['ma_cross'] = 0  # Neutral
            
        # Signal 2: Price vs Short MA
        if last_close > last_ma_short:
            signals['price_vs_ma_short'] = 1  # Bullish
        elif last_close < last_ma_short:
            signals['price_vs_ma_short'] = -1  # Bearish
        else:
            signals['price_vs_ma_short'] = 0  # Neutral
            
        # Signal 3: Price vs Mid MA
        if last_close > last_ma_mid:
            signals['price_vs_ma_mid'] = 1  # Bullish
        elif last_close < last_ma_mid:
            signals['price_vs_ma_mid'] = -1  # Bearish
        else:
            signals['price_vs_ma_mid'] = 0  # Neutral
            
        # Signal 4: MA slope (trend direction)
        ma_short_slope = price_data['ma_short'].iloc[-1] - price_data['ma_short'].iloc[-5]
        if ma_short_slope > 0:
            signals['ma_slope'] = 1  # Bullish
        elif ma_short_slope < 0:
            signals['ma_slope'] = -1  # Bearish
        else:
            signals['ma_slope'] = 0  # Neutral
            
        return signals
        
    def _calculate_rsi_signals(self, price_data):
        """Calculate RSI based signals"""
        signals = {}
        
        # Calculate RSI
        delta = price_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Avoid division by zero
        rs = gain / loss.where(loss != 0, 1)
        rsi = 100 - (100 / (1 + rs))
        
        price_data['rsi'] = rsi
        
        # Skip if not enough data
        if price_data['rsi'].isna().iloc[-1]:
            return signals
            
        last_rsi = price_data['rsi'].iloc[-1]
        
        # Signal 1: RSI overbought/oversold
        if last_rsi > 70:
            signals['rsi_overbought'] = -1  # Bearish
        elif last_rsi < 30:
            signals['rsi_oversold'] = 1  # Bullish
        else:
            signals['rsi_neutral'] = 0  # Neutral
            
        # Signal 2: RSI trend
        rsi_5_periods_ago = price_data['rsi'].iloc[-6] if len(price_data) > 5 else last_rsi
        if last_rsi > rsi_5_periods_ago:
            signals['rsi_trend'] = 1  # Bullish
        elif last_rsi < rsi_5_periods_ago:
            signals['rsi_trend'] = -1  # Bearish
        else:
            signals['rsi_trend'] = 0  # Neutral
            
        return signals
        
    def _calculate_macd_signals(self, price_data):
        """Calculate MACD based signals"""
        signals = {}
        
        # Calculate MACD
        ema_12 = price_data['close'].ewm(span=12, adjust=False).mean()
        ema_26 = price_data['close'].ewm(span=26, adjust=False).mean()
        
        price_data['macd'] = ema_12 - ema_26
        price_data['macd_signal'] = price_data['macd'].ewm(span=9, adjust=False).mean()
        price_data['macd_hist'] = price_data['macd'] - price_data['macd_signal']
        
        # Skip if not enough data
        if price_data['macd'].isna().iloc[-1] or price_data['macd_signal'].isna().iloc[-1]:
            return signals
            
        # Signal 1: MACD vs Signal line
        last_macd = price_data['macd'].iloc[-1]
        last_signal = price_data['macd_signal'].iloc[-1]
        
        if last_macd > last_signal:
            signals['macd_cross'] = 1  # Bullish
        elif last_macd < last_signal:
            signals['macd_cross'] = -1  # Bearish
        else:
            signals['macd_cross'] = 0  # Neutral
            
        # Signal 2: MACD histogram direction
        last_hist = price_data['macd_hist'].iloc[-1]
        prev_hist = price_data['macd_hist'].iloc[-2] if len(price_data) > 1 else 0
        
        if last_hist > prev_hist:
            signals['macd_hist_dir'] = 1  # Bullish
        elif last_hist < prev_hist:
            signals['macd_hist_dir'] = -1  # Bearish
        else:
            signals['macd_hist_dir'] = 0  # Neutral
            
        # Signal 3: MACD above/below zero
        if last_macd > 0:
            signals['macd_above_zero'] = 1  # Bullish
        elif last_macd < 0:
            signals['macd_below_zero'] = -1  # Bearish
        else:
            signals['macd_zero'] = 0  # Neutral
            
        return signals
        
    def _calculate_price_action_signals(self, price_data):
        """Calculate price action based signals"""
        signals = {}
        
        # Get recent candles
        if len(price_data) < 3:
            return signals
            
        last_candle = price_data.iloc[-1]
        prev_candle = price_data.iloc[-2]
        third_candle = price_data.iloc[-3]
        
        # Signal 1: Bullish/Bearish candle
        if last_candle['close'] > last_candle['open']:
            signals['last_candle'] = 1  # Bullish
        elif last_candle['close'] < last_candle['open']:
            signals['last_candle'] = -1  # Bearish
        else:
            signals['last_candle'] = 0  # Neutral
            
        # Signal 2: Higher highs / Lower lows (basic trend)
        if last_candle['high'] > prev_candle['high'] and prev_candle['high'] > third_candle['high']:
            signals['higher_highs'] = 1  # Bullish
        elif last_candle['low'] < prev_candle['low'] and prev_candle['low'] < third_candle['low']:
            signals['lower_lows'] = -1  # Bearish
            
        # Signal 3: Engulfing patterns
        # Bullish engulfing
        if (prev_candle['close'] < prev_candle['open'] and  # Previous candle is bearish
            last_candle['close'] > last_candle['open'] and  # Current candle is bullish
            last_candle['open'] <= prev_candle['close'] and  # Current open <= previous close
            last_candle['close'] >= prev_candle['open']):   # Current close >= previous open
            signals['bullish_engulfing'] = 1
            
        # Bearish engulfing
        elif (prev_candle['close'] > prev_candle['open'] and  # Previous candle is bullish
              last_candle['close'] < last_candle['open'] and  # Current candle is bearish
              last_candle['open'] >= prev_candle['close'] and  # Current open >= previous close
              last_candle['close'] <= prev_candle['open']):   # Current close <= previous open
            signals['bearish_engulfing'] = -1
            
        return signals
        
    def _calculate_volatility_signals(self, price_data):
        """Calculate volatility based signals"""
        signals = {}
        
        # Calculate Bollinger Bands
        price_data['ma20'] = price_data['close'].rolling(window=20).mean()
        price_data['std20'] = price_data['close'].rolling(window=20).std()
        price_data['upper_band'] = price_data['ma20'] + (price_data['std20'] * 2)
        price_data['lower_band'] = price_data['ma20'] - (price_data['std20'] * 2)
        
        # Skip if not enough data
        if price_data['ma20'].isna().iloc[-1]:
            return signals
            
        last_close = price_data['close'].iloc[-1]
        last_upper = price_data['upper_band'].iloc[-1]
        last_lower = price_data['lower_band'].iloc[-1]
        
        # Signal 1: Price near Bollinger Bands
        if last_close > last_upper:
            signals['bb_upper'] = -1  # Overbought, bearish
        elif last_close < last_lower:
            signals['bb_lower'] = 1  # Oversold, bullish
            
        # Signal 2: Bollinger Band width (volatility)
        band_width = (last_upper - last_lower) / price_data['ma20'].iloc[-1]
        avg_band_width = ((price_data['upper_band'] - price_data['lower_band']) / price_data['ma20']).mean()
        
        if band_width < avg_band_width * 0.8:
            signals['bb_squeeze'] = 0  # Neutral, but potential breakout coming
            
        return signals
        
    def format_recommendation_output(self, recommendation):
        """Format the recommendation output for display"""
        symbol = recommendation["symbol"]
        rec = recommendation["recommendation"]
        
        # Determine color based on recommendation
        color = "yellow"
        if rec == "LONG":
            color = "green"
        elif rec == "SHORT":
            color = "red"
            
        # Format output
        output = []
        output.append(f"📊 Position Recommendation for {symbol}")
        output.append(f"🔍 Recommendation: {rec}")
        output.append(f"⚖️ Confidence: {recommendation['confidence']:.2f}")
        
        if recommendation["entry_price"]:
            output.append(f"💰 Entry Price: {recommendation['entry_price']}")
            
        if recommendation["stop_loss"]:
            output.append(f"🛑 Stop Loss: {recommendation['stop_loss']}")
            
        if recommendation["take_profit"]:
            output.append(f"🎯 Take Profit: {recommendation['take_profit']}")
            
        if recommendation["risk_reward_ratio"]:
            output.append(f"📏 Risk/Reward: 1:{recommendation['risk_reward_ratio']}")
            
        # Add top reasons
        if recommendation["analysis"]["reasons"]:
            output.append(f"🧠 Analysis:")
            for reason in recommendation["analysis"]["reasons"][:5]:  # Show top 5 reasons
                output.append(f"  • {reason}")
                
        return output, color 