"""
Alpaca-based position management utility for tracking open trades
"""
import os
import json
from datetime import datetime
import pandas as pd
from termcolor import cprint
from src.utils.alpaca_client import AlpacaClient
from src.config import MAX_POSITION_SIZE, MAX_DAILY_LOSS, MAX_OPEN_POSITIONS

class AlpacaPositionManager:
    def __init__(self, data_dir='data'):
        self.client = AlpacaClient()
        self.history = []
        self.daily_pl = 0
        self.data_dir = data_dir
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        self.history_file = os.path.join(data_dir, 'trade_history.json')
        
        # Load existing trade history if available
        self.load_history()
        
    def load_history(self):
        """Load trade history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
                cprint(f"📋 Loaded {len(self.history)} trade records from file", "green")
        except Exception as e:
            cprint(f"❌ Error loading trade history: {str(e)}", "red")
    
    def save_history(self):
        """Save trade history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            cprint(f"❌ Error saving trade history: {str(e)}", "red")
    
    def get_positions(self):
        """Get all currently open positions from Alpaca"""
        if not self.client.is_configured:
            cprint(f"⚠️ Alpaca API not configured, returning empty positions", "yellow")
            return []
            
        try:
            positions = self.client.get_positions()
            
            # Format positions to match our system's format
            formatted_positions = []
            for p in positions:
                # Convert Alpaca position format to our internal format
                formatted_pos = {
                    'pair': p['symbol'],
                    'direction': 'buy' if p['side'] == 'long' else 'sell',
                    'entry_price': p['avg_entry_price'],
                    'size': p['qty'],
                    'unrealized_pl': p['unrealized_pl'],
                    'market_value': p['market_value'],
                    'current_price': p['current_price']
                }
                
                formatted_positions.append(formatted_pos)
                
            return formatted_positions
        except Exception as e:
            cprint(f"❌ Error fetching positions from Alpaca: {str(e)}", "red")
            return []
    
    def open_position(self, pair, direction, entry_price, size, stop_loss=None, take_profit=None):
        """Record a new position (actual execution done through order executor)"""
        # Record the trade entry for our history
        entry_record = {
            'pair': pair,
            'direction': direction,
            'entry_price': entry_price,
            'size': size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now().isoformat(),
            'status': 'open',
            'exit_price': None,
            'exit_time': None,
            'pips': None,
            'pl_amount': None,
            'reason': None
        }
        
        self.history.append(entry_record)
        self.save_history()
        
        cprint(f"✅ Recorded {direction.upper()} position for {pair} at {entry_price}", "green")
        return entry_record
    
    def close_position(self, pair, exit_price=None, reason="manual"):
        """Record a position closure (actual execution done through order executor)"""
        # Find the most recent open position for this pair
        open_position = None
        position_index = None
        
        for idx, trade in enumerate(reversed(self.history)):
            if trade['pair'] == pair and trade['status'] == 'open':
                open_position = trade
                position_index = len(self.history) - 1 - idx
                break
        
        if not open_position:
            cprint(f"❌ No open position record found for {pair}", "red")
            return None
        
        # If exit price not provided, get it from Alpaca
        if exit_price is None and self.client.is_configured:
            exit_price = self.client.get_current_price(pair)
            
        # If still None, use the entry price as fallback
        if exit_price is None:
            exit_price = open_position['entry_price']
        
        # Calculate profit/loss
        pip_value = 0.0001 if "JPY" not in pair else 0.01
        if open_position['direction'].lower() in ['buy', 'long']:
            pips = (exit_price - open_position['entry_price']) / pip_value
        else:
            pips = (open_position['entry_price'] - exit_price) / pip_value
            
        pl_amount = pips * float(open_position['size'])
        
        # Update the trade record
        self.history[position_index]['exit_price'] = exit_price
        self.history[position_index]['exit_time'] = datetime.now().isoformat()
        self.history[position_index]['pips'] = pips
        self.history[position_index]['pl_amount'] = pl_amount
        self.history[position_index]['reason'] = reason
        self.history[position_index]['status'] = 'closed'
        
        # Update daily P/L
        self.daily_pl += pl_amount
        
        # Save trade history
        self.save_history()
        
        pl_color = "green" if pl_amount >= 0 else "red"
        cprint(f"💰 Recorded close of {pair} position for {pl_amount:.2f} profit/loss ({pips:.1f} pips)", pl_color)
        
        return self.history[position_index]
    
    def get_position_summary(self):
        """Get summary of all open positions from Alpaca"""
        positions = self.get_positions()
        
        return pd.DataFrame(positions) if positions else pd.DataFrame()
    
    def get_trade_history(self, days=7):
        """Get trade history for the last N days"""
        df = pd.DataFrame(self.history) if self.history else pd.DataFrame()
        
        if not df.empty and 'entry_time' in df.columns:
            # Convert entry_time to datetime
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            
            # Filter to last N days
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            df = df[df['entry_time'] >= cutoff_date]
            
        return df
    
    def calculate_position_size(self, pair, entry_price, stop_loss):
        """Calculate safe position size based on risk parameters"""
        # Get account info from Alpaca if available
        if self.client.is_configured:
            account_info = self.client.get_account_info()
            account_balance = float(account_info.get('equity', 10000))
        else:
            # Default account balance for simulation
            account_balance = 10000  
        
        # Risk amount (e.g., 2% of account)
        risk_amount = account_balance * MAX_POSITION_SIZE
        
        # Calculate pip value
        pip_value = 0.0001 if "JPY" not in pair else 0.01
        
        # Calculate stop distance in pips
        stop_distance = abs(entry_price - stop_loss) / pip_value
        
        if stop_distance == 0:
            cprint(f"⚠️ Invalid stop distance for {pair}", "yellow")
            return 0
        
        # Calculate position size (units)
        # This is a simplified calculation - in real trading, you'd need to account for:
        # - Currency conversion if account is not in the same currency
        # - Lot sizes and minimum transaction sizes
        position_size = (risk_amount / stop_distance) * 100
        
        # Round to 2 decimal places for stocks, whole number for forex
        if '/' in pair:  # Forex
            position_size = round(position_size)
        else:  # Stocks
            position_size = round(position_size, 2)
        
        cprint(f"📊 Position size for {pair}: {position_size} units (risking ${risk_amount:.2f})", "blue")
        return position_size 