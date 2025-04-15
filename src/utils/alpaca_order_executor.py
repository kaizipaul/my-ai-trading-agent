"""
Alpaca Markets order execution utility for placing trade orders
"""
import os
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv
from src.utils.alpaca_client import AlpacaClient

# Load environment variables if not already loaded
load_dotenv()

class AlpacaOrderExecutor:
    def __init__(self):
        self.client = AlpacaClient()
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    def place_market_order(self, pair, direction, units, stop_loss=None, take_profit=None):
        """Place a market order"""
        # In development mode with API not configured, just simulate the order
        if self.environment == "development" and not self.client.is_configured:
            cprint(f"🔵 [SIMULATION] Placing {direction} order for {pair}, {units} units", "blue")
            # Return a simulated order ID
            return {
                "orderId": f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "status": "FILLED",
                "pair": pair,
                "direction": direction,
                "units": units,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
        
        # Use Alpaca client to place the order
        try:
            # Make sure direction is lowercase for Alpaca
            direction = direction.lower()
            if direction not in ['buy', 'sell']:
                direction = 'buy' if direction == 'long' else 'sell'
                
            response = self.client.place_market_order(
                pair, 
                direction, 
                units, 
                stop_loss, 
                take_profit
            )
            
            if not response or "error" in response:
                cprint(f"❌ Error placing order with Alpaca: {response.get('error', 'Unknown error')}", "red")
                return None
                
            cprint(f"✅ Order placed: {response.get('order_id', 'N/A')}", "green")
            
            # Map the response to a standard format for our system
            return {
                "orderId": response.get('order_id', f"unknown-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "status": response.get('status', "FILLED"),
                "pair": pair,
                "direction": direction,
                "units": units,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
            
        except Exception as e:
            cprint(f"❌ Error placing order: {str(e)}", "red")
            return None
            
    def close_trade(self, symbol):
        """Close an existing trade"""
        # In development mode with API not configured, just simulate the close
        if self.environment == "development" and not self.client.is_configured:
            cprint(f"🔵 [SIMULATION] Closing trade for {symbol}", "blue")
            return {
                "status": "CLOSED",
                "symbol": symbol
            }
        
        # Use Alpaca client to close the position
        try:
            response = self.client.close_position(symbol)
            
            if not response or "error" in response:
                cprint(f"❌ Error closing position with Alpaca: {response.get('error', 'Unknown error')}", "red")
                return None
                
            cprint(f"✅ Position closed for {symbol}", "green")
            return {
                "status": "CLOSED",
                "symbol": symbol,
                "qty": response.get('qty', 0)
            }
            
        except Exception as e:
            cprint(f"❌ Error closing trade: {str(e)}", "red")
            return None
            
    def close_all_positions(self):
        """Close all open positions"""
        # In development mode with API not configured, just simulate
        if self.environment == "development" and not self.client.is_configured:
            cprint(f"🔵 [SIMULATION] Closing all positions", "blue")
            return {"status": "CLOSED_ALL"}
        
        # Use Alpaca client to close all positions
        try:
            response = self.client.close_all_positions()
            
            if not response or "error" in response:
                cprint(f"❌ Error closing positions with Alpaca: {response.get('error', 'Unknown error')}", "red")
                return None
                
            cprint(f"✅ All positions closed", "green")
            return {"status": "CLOSED_ALL"}
            
        except Exception as e:
            cprint(f"❌ Error closing all positions: {str(e)}", "red")
            return None
            
    def modify_trade(self, symbol, stop_loss=None, take_profit=None):
        """Modify an existing trade's stop loss or take profit"""
        # In development mode with API not configured, just simulate
        if self.environment == "development" and not self.client.is_configured:
            cprint(f"🔵 [SIMULATION] Modifying trade for {symbol}", "blue")
            return {
                "status": "MODIFIED",
                "symbol": symbol,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
        
        # Get current position details
        position = self.client.get_position(symbol)
        if not position:
            cprint(f"❌ No open position found for {symbol}", "red")
            return None
            
        # Cancel existing stop loss and take profit orders
        orders = self.client.get_orders()
        for order in orders:
            if order['symbol'] == symbol and order['type'] in ['stop', 'limit']:
                self.client.cancel_order(order['id'])
                
        # Place new stop loss order
        if stop_loss:
            side = 'sell' if position['side'] == 'long' else 'buy'
            self.client._place_stop_loss(symbol, position['side'], abs(float(position['qty'])), stop_loss)
            
        # Place new take profit order
        if take_profit:
            side = 'sell' if position['side'] == 'long' else 'buy'
            self.client._place_take_profit(symbol, position['side'], abs(float(position['qty'])), take_profit)
            
        cprint(f"✅ Position modified for {symbol}", "green")
        return {
            "status": "MODIFIED",
            "symbol": symbol,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
    
    def get_current_positions(self):
        """Get current open positions"""
        if self.environment == "development" and not self.client.is_configured:
            # Return empty list in simulation mode
            return []
            
        return self.client.get_positions()
        
    def get_account_info(self):
        """Get account information"""
        if self.environment == "development" and not self.client.is_configured:
            # Return simulated account info
            return {
                "account_id": "simulated-account",
                "cash": 100000.0,
                "portfolio_value": 100000.0,
                "buying_power": 100000.0,
                "equity": 100000.0,
                "is_trading_blocked": False
            }
            
        return self.client.get_account_info() 