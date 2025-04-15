"""
Position management utility for tracking open trades
"""
import os
import json
from datetime import datetime
import pandas as pd
from termcolor import cprint
from src.config import MAX_POSITION_SIZE, MAX_DAILY_LOSS, MAX_OPEN_POSITIONS, STOP_LOSS_PIPS, TAKE_PROFIT_PIPS

class PositionManager:
    def __init__(self, data_dir='data'):
        self.positions = {}
        self.history = []
        self.daily_pl = 0
        self.data_dir = data_dir
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        self.positions_file = os.path.join(data_dir, 'positions.json')
        self.history_file = os.path.join(data_dir, 'trade_history.json')
        
        # Load existing positions if available
        self.load_positions()
        
    def load_positions(self):
        """Load positions from file"""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    self.positions = json.load(f)
                cprint(f"📋 Loaded {len(self.positions)} positions from file", "green")
        except Exception as e:
            cprint(f"❌ Error loading positions: {str(e)}", "red")
    
    def save_positions(self):
        """Save positions to file"""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            cprint(f"❌ Error saving positions: {str(e)}", "red")
    
    def open_position(self, pair, direction, entry_price, size, stop_loss=None, take_profit=None):
        """Open a new trading position"""
        # Calculate default stop loss and take profit if not provided
        if stop_loss is None:
            pip_value = 0.0001 if "JPY" not in pair else 0.01
            stop_loss = entry_price - (STOP_LOSS_PIPS * pip_value) if direction == 'buy' else entry_price + (STOP_LOSS_PIPS * pip_value)
            
        if take_profit is None:
            pip_value = 0.0001 if "JPY" not in pair else 0.01
            take_profit = entry_price + (TAKE_PROFIT_PIPS * pip_value) if direction == 'buy' else entry_price - (TAKE_PROFIT_PIPS * pip_value)
        
        position = {
            'pair': pair,
            'direction': direction,
            'entry_price': entry_price,
            'size': size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now().isoformat(),
            'unrealized_pl': 0
        }
        
        self.positions[pair] = position
        self.save_positions()
        
        cprint(f"✅ Opened {direction.upper()} position for {pair} at {entry_price}", "green")
        return position
    
    def close_position(self, pair, exit_price=None, reason="manual"):
        """Close an open position"""
        if pair not in self.positions:
            cprint(f"❌ No open position for {pair}", "red")
            return None
        
        position = self.positions[pair]
        
        # If exit price not provided, assume current market price (for manual closures)
        if exit_price is None:
            # In a real system, this would fetch the current market price
            exit_price = position['entry_price']  # Placeholder
            
        # Calculate profit/loss
        pip_value = 0.0001 if "JPY" not in pair else 0.01
        pips = (exit_price - position['entry_price']) / pip_value if position['direction'] == 'buy' else (position['entry_price'] - exit_price) / pip_value
        pl_amount = pips * position['size']
        
        # Record trade in history
        trade_record = {
            **position,
            'exit_price': exit_price,
            'exit_time': datetime.now().isoformat(),
            'pips': pips,
            'pl_amount': pl_amount,
            'reason': reason
        }
        
        self.history.append(trade_record)
        
        # Update daily P/L
        self.daily_pl += pl_amount
        
        # Remove from active positions
        del self.positions[pair]
        self.save_positions()
        
        # Save trade history
        self.save_history()
        
        pl_color = "green" if pl_amount >= 0 else "red"
        cprint(f"💰 Closed {pair} position for {pl_amount:.2f} profit/loss ({pips:.1f} pips)", pl_color)
        
        return trade_record
    
    def update_position(self, pair, current_price):
        """Update position with current market price"""
        if pair not in self.positions:
            return None
            
        position = self.positions[pair]
        
        # Check if stop loss or take profit hit
        if position['direction'] == 'buy':
            if current_price <= position['stop_loss']:
                return self.close_position(pair, current_price, "stop_loss")
            elif current_price >= position['take_profit']:
                return self.close_position(pair, current_price, "take_profit")
        else:  # sell position
            if current_price >= position['stop_loss']:
                return self.close_position(pair, current_price, "stop_loss")
            elif current_price <= position['take_profit']:
                return self.close_position(pair, current_price, "take_profit")
        
        # Update unrealized P/L
        pip_value = 0.0001 if "JPY" not in pair else 0.01
        pips = (current_price - position['entry_price']) / pip_value if position['direction'] == 'buy' else (position['entry_price'] - current_price) / pip_value
        position['unrealized_pl'] = pips * position['size']
        
        self.positions[pair] = position
        return position
    
    def save_history(self):
        """Save trade history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            cprint(f"❌ Error saving trade history: {str(e)}", "red")
    
    def get_position_summary(self):
        """Get summary of all open positions"""
        return pd.DataFrame(self.positions).T if self.positions else pd.DataFrame()
    
    def get_trade_history(self, days=7):
        """Get trade history for the last N days"""
        return pd.DataFrame(self.history) if self.history else pd.DataFrame()
    
    def calculate_position_size(self, pair, entry_price, stop_loss):
        """Calculate safe position size based on risk parameters"""
        # Default account balance - in a real system, this would be fetched from the broker
        account_balance = 10000  # Example account balance of $10,000
        
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
        
        cprint(f"📊 Position size for {pair}: {position_size:.2f} units (risking ${risk_amount:.2f})", "blue")
        return position_size
