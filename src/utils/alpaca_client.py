"""
Alpaca Markets API client for executing trades and managing positions
"""
import os
import time
import logging
from datetime import datetime
from termcolor import cprint
import pandas as pd
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AlpacaClient:
    def __init__(self):
        """Initialize the Alpaca API client"""
        # Get API credentials from environment variables
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.api_secret = os.getenv("ALPACA_API_SECRET")
        self.base_url = os.getenv("ALPACA_API_URL", "https://paper-api.alpaca.markets")
        
        # Check if credentials are provided
        if not self.api_key or not self.api_secret:
            cprint("⚠️ Alpaca API credentials not found in environment variables", "yellow")
            cprint("🔑 Please set ALPACA_API_KEY and ALPACA_API_SECRET in .env file", "yellow")
            self.is_configured = False
        else:
            self.is_configured = True
            
            # Initialize Alpaca API
            try:
                self.api = tradeapi.REST(
                    self.api_key,
                    self.api_secret,
                    self.base_url,
                    api_version='v2'
                )
                self.account = self.api.get_account()
                cprint(f"✅ Connected to Alpaca API ({self.base_url})", "green")
                cprint(f"💰 Account: ${float(self.account.cash):.2f} available", "green")
            except Exception as e:
                cprint(f"❌ Failed to connect to Alpaca API: {str(e)}", "red")
                self.is_configured = False
    
    def get_account_info(self):
        """Get account information"""
        if not self.is_configured:
            return {"error": "API not configured"}
            
        try:
            self.account = self.api.get_account()
            return {
                "account_id": self.account.id,
                "cash": float(self.account.cash),
                "portfolio_value": float(self.account.portfolio_value),
                "buying_power": float(self.account.buying_power),
                "equity": float(self.account.equity),
                "is_trading_blocked": self.account.trading_blocked
            }
        except Exception as e:
            cprint(f"❌ Error getting account info: {str(e)}", "red")
            return {"error": str(e)}
    
    def get_positions(self):
        """Get all open positions"""
        if not self.is_configured:
            return []
            
        try:
            positions = self.api.list_positions()
            return [{
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "side": p.side
            } for p in positions]
        except Exception as e:
            cprint(f"❌ Error getting positions: {str(e)}", "red")
            return []
    
    def get_position(self, symbol):
        """Get specific position for a symbol"""
        if not self.is_configured:
            return None
            
        try:
            position = self.api.get_position(symbol)
            return {
                "symbol": position.symbol,
                "qty": float(position.qty),
                "avg_entry_price": float(position.avg_entry_price),
                "current_price": float(position.current_price),
                "market_value": float(position.market_value),
                "unrealized_pl": float(position.unrealized_pl),
                "unrealized_plpc": float(position.unrealized_plpc),
                "side": position.side
            }
        except Exception as e:
            # Position doesn't exist
            return None
    
    def get_current_price(self, symbol):
        """Get current market price for a symbol"""
        if not self.is_configured:
            return None
            
        try:
            # Convert forex symbols if needed (e.g., EUR/USD to EUR-USD)
            symbol = self._format_symbol(symbol)
            
            # Get last quote
            quote = self.api.get_latest_quote(symbol)
            
            # Return mid price (between bid and ask)
            return (float(quote.bidprice) + float(quote.askprice)) / 2
        except Exception as e:
            cprint(f"❌ Error getting price for {symbol}: {str(e)}", "red")
            return None
    
    def get_market_data(self, symbol, timeframe='1D', limit=100):
        """Get historical market data for a symbol"""
        if not self.is_configured:
            return None
            
        try:
            # Convert forex symbols if needed
            symbol = self._format_symbol(symbol)
            
            # Map timeframe to Alpaca format
            timeframe_map = {
                '1m': '1Min',
                '5m': '5Min',
                '15m': '15Min',
                '30m': '30Min',
                '1h': '1H',
                '1d': '1D',
                '1D': '1D',
                '1w': '1W'
            }
            
            alpaca_timeframe = timeframe_map.get(timeframe, '1D')
            
            # Get the data
            bars = self.api.get_bars(
                symbol, 
                alpaca_timeframe, 
                limit=limit
            ).df
            
            if len(bars) > 0:
                # Rename columns to match our system
                bars = bars.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                
                return bars
            else:
                cprint(f"⚠️ No data found for {symbol}", "yellow")
                return None
                
        except Exception as e:
            cprint(f"❌ Error getting market data for {symbol}: {str(e)}", "red")
            return None
    
    def place_market_order(self, symbol, side, qty, stop_loss=None, take_profit=None):
        """Place a market order"""
        if not self.is_configured:
            return {"error": "API not configured"}
            
        try:
            # Convert forex symbols if needed
            symbol = self._format_symbol(symbol)
            
            # Place the order
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,  # 'buy' or 'sell'
                type='market',
                time_in_force='gtc'  # Good 'til canceled
            )
            
            order_id = order.id
            
            # If stop loss or take profit provided, wait for the order to fill
            # and then create bracket orders
            if (stop_loss or take_profit) and order_id:
                # Wait for fill
                filled_order = self._wait_for_order_fill(order_id)
                
                if filled_order and filled_order.status == 'filled':
                    # Place stop loss
                    if stop_loss:
                        self._place_stop_loss(symbol, side, qty, stop_loss)
                    
                    # Place take profit
                    if take_profit:
                        self._place_take_profit(symbol, side, qty, take_profit)
            
            cprint(f"✅ {side.upper()} order placed for {qty} {symbol}", "green")
            
            return {
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "status": order.status
            }
        except Exception as e:
            cprint(f"❌ Error placing market order: {str(e)}", "red")
            return {"error": str(e)}
    
    def _place_stop_loss(self, symbol, entry_side, qty, stop_price):
        """Place a stop loss order"""
        try:
            # The stop loss side is opposite of the entry
            side = 'sell' if entry_side == 'buy' else 'buy'
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='stop',
                time_in_force='gtc',
                stop_price=stop_price
            )
            
            cprint(f"✅ Stop loss set at {stop_price} for {symbol}", "green")
            return order.id
        except Exception as e:
            cprint(f"❌ Error setting stop loss: {str(e)}", "red")
            return None
    
    def _place_take_profit(self, symbol, entry_side, qty, take_profit_price):
        """Place a take profit order"""
        try:
            # The take profit side is opposite of the entry
            side = 'sell' if entry_side == 'buy' else 'buy'
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='limit',
                time_in_force='gtc',
                limit_price=take_profit_price
            )
            
            cprint(f"✅ Take profit set at {take_profit_price} for {symbol}", "green")
            return order.id
        except Exception as e:
            cprint(f"❌ Error setting take profit: {str(e)}", "red")
            return None
    
    def _wait_for_order_fill(self, order_id, max_wait=30):
        """Wait for an order to fill before placing bracket orders"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                order = self.api.get_order(order_id)
                if order.status == 'filled':
                    return order
                time.sleep(1)
            except Exception as e:
                cprint(f"❌ Error checking order status: {str(e)}", "red")
                return None
                
        cprint(f"⚠️ Order not filled after {max_wait} seconds", "yellow")
        return None
    
    def close_position(self, symbol):
        """Close an open position"""
        if not self.is_configured:
            return {"error": "API not configured"}
            
        try:
            # Convert forex symbols if needed
            symbol = self._format_symbol(symbol)
            
            # Close the position
            response = self.api.close_position(symbol)
            
            cprint(f"✅ Position closed for {symbol}", "green")
            
            return {
                "symbol": symbol,
                "status": "closed",
                "qty": float(response.qty)
            }
        except Exception as e:
            cprint(f"❌ Error closing position: {str(e)}", "red")
            return {"error": str(e)}
    
    def close_all_positions(self):
        """Close all open positions"""
        if not self.is_configured:
            return {"error": "API not configured"}
            
        try:
            response = self.api.close_all_positions()
            
            cprint(f"✅ All positions closed", "green")
            
            return {"status": "all positions closed"}
        except Exception as e:
            cprint(f"❌ Error closing all positions: {str(e)}", "red")
            return {"error": str(e)}
    
    def get_orders(self, status='open'):
        """Get all orders with a given status"""
        if not self.is_configured:
            return []
            
        try:
            orders = self.api.list_orders(status=status)
            
            return [{
                "id": o.id,
                "symbol": o.symbol,
                "side": o.side,
                "qty": float(o.qty),
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "stop_price": float(o.stop_price) if o.stop_price else None,
                "type": o.type,
                "status": o.status,
                "created_at": o.created_at
            } for o in orders]
        except Exception as e:
            cprint(f"❌ Error getting orders: {str(e)}", "red")
            return []
    
    def cancel_order(self, order_id):
        """Cancel an open order"""
        if not self.is_configured:
            return {"error": "API not configured"}
            
        try:
            self.api.cancel_order(order_id)
            cprint(f"✅ Order {order_id} canceled", "green")
            return {"status": "canceled", "order_id": order_id}
        except Exception as e:
            cprint(f"❌ Error canceling order: {str(e)}", "red")
            return {"error": str(e)}
    
    def _format_symbol(self, symbol):
        """Format symbol for Alpaca API (e.g., convert EUR/USD to EUR-USD)"""
        if '/' in symbol:
            # Forex pair - replace slash with hyphen
            return symbol.replace('/', '-')
        return symbol 