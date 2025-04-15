"""
Order execution utility for placing trade orders
"""
import os
import requests
import json
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv
from src.utils.forex_dot_com_client import ForexDotComClient

# Load environment variables if not already loaded
load_dotenv()

class OrderExecutor:
    def __init__(self):
        self.client = ForexDotComClient()
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    def place_market_order(self, pair, direction, units, stop_loss=None, take_profit=None):
        """Place a market order"""
        # In development mode, just simulate the order
        if self.environment == "development":
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
            
        # In production, place a real order
        try:
            # Format pair for FOREX.com
            formatted_pair = self.client.format_symbol(pair)
            
            # Place order using the client
            response = self.client.place_market_order(
                formatted_pair, 
                direction, 
                units, 
                stop_loss, 
                take_profit
            )
            
            if not response:
                cprint(f"❌ No response from FOREX.com when placing order", "red")
                return None
                
            cprint(f"✅ Order placed: {response.get('orderCreateTransaction', {}).get('id', 'N/A')}", "green")
            
            # Map the response to a standard format for our system
            return {
                "orderId": response.get('orderCreateTransaction', {}).get('id', f"unknown-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "status": response.get('orderFillTransaction', {}).get('type', "FILLED"),
                "pair": pair,
                "direction": direction,
                "units": units,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
            
        except Exception as e:
            cprint(f"❌ Error placing order: {str(e)}", "red")
            return None
            
    def close_trade(self, trade_id):
        """Close an existing trade"""
        # In development mode, just simulate the close
        if self.environment == "development":
            cprint(f"🔵 [SIMULATION] Closing trade {trade_id}", "blue")
            return {
                "status": "CLOSED",
                "trade_id": trade_id
            }
            
        # In production, close a real trade
        try:
            response = self.client.close_trade(trade_id)
            
            if not response:
                cprint(f"❌ No response from FOREX.com when closing trade", "red")
                return None
                
            cprint(f"✅ Trade closed: {trade_id}", "green")
            return {
                "status": "CLOSED",
                "trade_id": trade_id
            }
            
        except Exception as e:
            cprint(f"❌ Error closing trade: {str(e)}", "red")
            return None
            
    def close_all_positions(self):
        """Close all open positions"""
        # In development mode, just simulate
        if self.environment == "development":
            cprint(f"🔵 [SIMULATION] Closing all positions", "blue")
            return {"status": "CLOSED_ALL"}
            
        # In production, close all real positions
        try:
            response = self.client.close_all_positions()
            
            if not response:
                cprint(f"❌ No response from FOREX.com when closing all positions", "red")
                return None
                
            cprint(f"✅ All positions closed", "green")
            return {"status": "CLOSED_ALL"}
            
        except Exception as e:
            cprint(f"❌ Error closing all positions: {str(e)}", "red")
            return None
            
    def modify_trade(self, trade_id, stop_loss=None, take_profit=None):
        """Modify an existing trade's stop loss or take profit"""
        # In development mode, just simulate
        if self.environment == "development":
            cprint(f"🔵 [SIMULATION] Modifying trade {trade_id}", "blue")
            return {
                "status": "MODIFIED",
                "trade_id": trade_id,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
            
        # In production, modify a real trade
        try:
            response = self.client.modify_trade(trade_id, stop_loss, take_profit)
            
            if not response:
                cprint(f"❌ No response from FOREX.com when modifying trade", "red")
                return None
                
            cprint(f"✅ Trade modified: {trade_id}", "green")
            return {
                "status": "MODIFIED",
                "trade_id": trade_id,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
            
        except Exception as e:
            cprint(f"❌ Error modifying trade: {str(e)}", "red")
            return None
