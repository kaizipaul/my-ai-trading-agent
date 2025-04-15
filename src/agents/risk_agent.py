"""
Risk management agent for forex trading
"""
from datetime import datetime
import pandas as pd
from termcolor import cprint
from src.config import MAX_POSITION_SIZE, MAX_DAILY_LOSS, MAX_OPEN_POSITIONS

class ForexRiskAgent:
    def __init__(self):
        self.open_positions = {}
        self.daily_pl = 0
        self.last_reset = datetime.now().date()
        
    def run(self):
        """Main risk management cycle"""
        try:
            # Reset daily P/L if it's a new day
            current_date = datetime.now().date()
            if current_date > self.last_reset:
                self.daily_pl = 0
                self.last_reset = current_date
                
            # Check overall risk metrics
            self.check_risk_metrics()
            
        except Exception as e:
            cprint(f"❌ Error in risk management: {str(e)}", "red")
            
    def check_risk_metrics(self):
        """Check various risk metrics"""
        # Check daily loss limit
        if abs(self.daily_pl) > MAX_DAILY_LOSS:
            cprint("⚠️ Daily loss limit reached! No new trades allowed.", "red")
            return False
            
        # Check number of open positions
        if len(self.open_positions) >= MAX_OPEN_POSITIONS:
            cprint("⚠️ Maximum number of open positions reached!", "yellow")
            return False
            
        return True
        
    def can_trade(self, pair):
        """Check if we can trade a specific pair"""
        # Check if we already have a position
        if pair in self.open_positions:
            return False
            
        # Check overall risk metrics
        return self.check_risk_metrics()
        
    def calculate_position_size(self, pair, entry_price, stop_loss):
        """Calculate safe position size based on risk parameters"""
        risk_amount = MAX_POSITION_SIZE  # 2% of account
        stop_distance = abs(entry_price - stop_loss)
        
        if stop_distance == 0:
            return 0
            
        position_size = (risk_amount / stop_distance)
        return position_size