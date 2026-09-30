"""
Risk management agent for forex trading

Gates trade execution against real account state (open positions, equity,
realized + unrealized P/L) pulled from Alpaca, rather than local counters
that are never populated.
"""
from datetime import datetime
from termcolor import cprint
from src.config import MAX_DAILY_LOSS, MAX_OPEN_POSITIONS
from src.utils import log_info, log_warning, log_error
from src.utils.alpaca_position_manager import AlpacaPositionManager

# Fallback equity used only when Alpaca isn't configured (matches the
# simulated account balance used elsewhere in simulation/dev mode).
SIMULATED_ACCOUNT_EQUITY = 10000.0


class ForexRiskAgent:
    def __init__(self, position_manager=None):
        # Share the caller's position manager when given, so position/history
        # state stays consistent with whatever is executing trades.
        self.position_manager = position_manager or AlpacaPositionManager()
        self.client = self.position_manager.client
        self.last_reset = datetime.now().date()

    def run(self):
        """Main risk management cycle"""
        try:
            # Reset daily bookkeeping if it's a new day
            current_date = datetime.now().date()
            if current_date > self.last_reset:
                self.last_reset = current_date

            self.check_risk_metrics()

        except Exception as e:
            log_error(f"Error in risk management: {str(e)}")
            cprint(f"❌ Error in risk management: {str(e)}", "red")

    def get_open_positions(self):
        """Get currently open positions from the shared position manager"""
        return self.position_manager.get_positions()

    def get_account_equity(self):
        """Get current account equity from Alpaca, falling back to the simulated balance"""
        if self.client.is_configured:
            account_info = self.client.get_account_info()
            if "equity" in account_info:
                return float(account_info["equity"])
        return SIMULATED_ACCOUNT_EQUITY

    def get_daily_pl(self):
        """
        Compute today's P/L in dollars: realized P/L from trades closed today
        plus unrealized P/L on currently open positions.
        """
        today = datetime.now().date()
        realized = 0.0

        for trade in self.position_manager.history:
            if trade.get("status") != "closed" or not trade.get("exit_time"):
                continue
            try:
                exit_date = datetime.fromisoformat(trade["exit_time"]).date()
            except ValueError:
                continue
            if exit_date == today:
                realized += trade.get("pl_amount") or 0.0

        unrealized = sum(
            float(p.get("unrealized_pl", 0) or 0) for p in self.get_open_positions()
        )

        return realized + unrealized

    def check_risk_metrics(self):
        """Check daily loss and open-position limits against real account state"""
        equity = self.get_account_equity()
        daily_pl = self.get_daily_pl()
        daily_loss_pct = (-daily_pl / equity) if equity > 0 else 0

        # Only losses count against the daily loss limit
        if daily_loss_pct > MAX_DAILY_LOSS:
            msg = (
                f"Daily loss limit reached! P/L: ${daily_pl:.2f} "
                f"({daily_loss_pct*100:.2f}% of ${equity:.2f} equity). No new trades allowed."
            )
            log_warning(msg)
            cprint(f"⚠️ {msg}", "red")
            return False

        open_positions = self.get_open_positions()
        if len(open_positions) >= MAX_OPEN_POSITIONS:
            msg = f"Maximum number of open positions reached! ({len(open_positions)}/{MAX_OPEN_POSITIONS})"
            log_warning(msg)
            cprint(f"⚠️ {msg}", "yellow")
            return False

        return True

    def can_trade(self, pair):
        """Check if we can open a new trade for a specific pair"""
        open_positions = self.get_open_positions()

        # Already have a position for this pair
        if any(p["pair"] == pair for p in open_positions):
            log_info(f"Risk check: already have an open position for {pair}")
            return False

        return self.check_risk_metrics()

    def calculate_position_size(self, pair, entry_price, stop_loss):
        """Calculate safe position size based on real account equity and risk parameters"""
        return self.position_manager.calculate_position_size(pair, entry_price, stop_loss)
