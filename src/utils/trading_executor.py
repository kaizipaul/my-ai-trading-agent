"""
Forex Trading Executor - Handles different trading actions
"""
from termcolor import cprint
import time
from enum import Enum

class TradingAction(Enum):
    CLOSE_POSITION = 0
    OPEN_POSITION = 1
    STOP_LOSS = 2
    BREAKOUT = 3
    MARKET_MAKER = 4

class ForexTradingExecutor:
    def __init__(self, broker_client, order_executor):
        self.broker = broker_client
        self.order_executor = order_executor
        
    def execute_action(self, action, pair, params):
        """Execute a trading action"""
        try:
            if action == TradingAction.CLOSE_POSITION:
                return self._close_position(pair)
            elif action == TradingAction.OPEN_POSITION:
                return self._open_position(pair, params)
            elif action == TradingAction.STOP_LOSS:
                return self._monitor_stop_loss(pair, params)
            elif action == TradingAction.BREAKOUT:
                return self._monitor_breakout(pair, params)
            elif action == TradingAction.MARKET_MAKER:
                return self._market_maker(pair, params)
            else:
                cprint(f"❌ Invalid action: {action}", "red")
                
        except Exception as e:
            cprint(f"❌ Error executing action: {str(e)}", "red")
            
    def _close_position(self, pair):
        """Close position in chunks"""
        cprint(f"🔄 Closing position for {pair}...", "cyan")
        position = self.broker.get_position_size(pair)
        
        while position > 0:
            self.order_executor.chunk_exit(pair)
            position = self.broker.get_position_size(pair)
            time.sleep(1)
            
        cprint(f"✅ Position closed for {pair}", "green")
        
    def _open_position(self, pair, params):
        """Open position in chunks"""
        target_size = params.get('size', 0)
        current_position = self.broker.get_position_size(pair)
        current_price = self.broker.get_current_price(pair)
        position_value = current_position * current_price
        
        if position_value >= (target_size * 0.97):
            cprint("✅ Position already filled", "green")
            return
            
        self.order_executor.elegant_entry(pair, target_size, params.get('buy_under', float('inf')))
        
    def _monitor_stop_loss(self, pair, params):
        """Monitor and execute stop loss"""
        stop_price = params.get('stop_price')
        while True:
            current_price = self.broker.get_current_price(pair)
            position = self.broker.get_position_size(pair)
            
            if current_price < stop_price and position > 0:
                cprint(f"🛑 Stop loss triggered for {pair} at {current_price}", "yellow")
                self._close_position(pair)
                break
                
            time.sleep(30)
            
    def _monitor_breakout(self, pair, params):
        """Monitor and execute breakout trades"""
        breakout_price = params.get('breakout_price')
        target_size = params.get('size', 0)
        
        while True:
            current_price = self.broker.get_current_price(pair)
            position = self.broker.get_position_size(pair)
            position_value = position * current_price
            
            if current_price > breakout_price and position_value < target_size:
                cprint(f"🚀 Breakout triggered for {pair} at {current_price}", "green")
                self._open_position(pair, {
                    'size': target_size,
                    'buy_over': breakout_price
                })
                
            time.sleep(30)
            
    def _market_maker(self, pair, params):
        """Market making strategy"""
        buy_under = params.get('buy_under')
        sell_over = params.get('sell_over')
        target_size = params.get('size', 0)
        
        while True:
            current_price = self.broker.get_current_price(pair)
            position = self.broker.get_position_size(pair)
            position_value = position * current_price
            
            if current_price > sell_over:
                cprint(f"📈 Selling {pair} above {sell_over}", "yellow")
                self._close_position(pair)
            elif current_price < buy_under and position_value < target_size:
                cprint(f"📉 Buying {pair} below {buy_under}", "green")
                self._open_position(pair, {
                    'size': target_size,
                    'buy_under': buy_under
                })
                
            time.sleep(30)