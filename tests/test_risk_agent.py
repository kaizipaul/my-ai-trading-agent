"""
Tests for ForexRiskAgent: daily loss limit, max open positions, and
per-symbol existing-position gating, against a fake position manager
(no real Alpaca calls).
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import src.config as config
from src.agents.risk_agent import ForexRiskAgent


def make_position_manager(equity=10000.0, positions=None, history=None, is_configured=True):
    pm = MagicMock()
    pm.client.is_configured = is_configured
    pm.client.get_account_info.return_value = {"equity": equity}
    pm.get_positions.return_value = positions or []
    pm.history = history or []
    return pm


def test_check_risk_metrics_passes_with_no_positions_no_loss():
    agent = ForexRiskAgent(position_manager=make_position_manager())
    assert agent.check_risk_metrics() is True


def test_check_risk_metrics_blocks_on_daily_loss_limit():
    # -600 / 10000 equity = 6% loss, over the 5% default MAX_DAILY_LOSS
    pm = make_position_manager(positions=[{'pair': 'AAPL', 'unrealized_pl': -600}])
    agent = ForexRiskAgent(position_manager=pm)
    assert agent.check_risk_metrics() is False


def test_check_risk_metrics_allows_small_loss_under_limit():
    # -100 / 10000 = 1% loss, under the 5% limit
    pm = make_position_manager(positions=[{'pair': 'AAPL', 'unrealized_pl': -100}])
    agent = ForexRiskAgent(position_manager=pm)
    assert agent.check_risk_metrics() is True


def test_check_risk_metrics_allows_profit_regardless_of_magnitude():
    pm = make_position_manager(positions=[{'pair': 'AAPL', 'unrealized_pl': 5000}])
    agent = ForexRiskAgent(position_manager=pm)
    assert agent.check_risk_metrics() is True


def test_check_risk_metrics_blocks_at_max_open_positions():
    positions = [{'pair': f'SYM{i}', 'unrealized_pl': 0} for i in range(config.MAX_OPEN_POSITIONS)]
    pm = make_position_manager(positions=positions)
    agent = ForexRiskAgent(position_manager=pm)
    assert agent.check_risk_metrics() is False


def test_check_risk_metrics_allows_under_max_open_positions():
    positions = [{'pair': f'SYM{i}', 'unrealized_pl': 0} for i in range(config.MAX_OPEN_POSITIONS - 1)]
    pm = make_position_manager(positions=positions)
    agent = ForexRiskAgent(position_manager=pm)
    assert agent.check_risk_metrics() is True


def test_can_trade_blocks_existing_position_in_same_pair():
    pm = make_position_manager(positions=[{'pair': 'EUR/USD', 'unrealized_pl': 0}])
    agent = ForexRiskAgent(position_manager=pm)
    assert agent.can_trade('EUR/USD') is False


def test_can_trade_allows_new_pair():
    pm = make_position_manager(positions=[{'pair': 'EUR/USD', 'unrealized_pl': 0}])
    agent = ForexRiskAgent(position_manager=pm)
    assert agent.can_trade('GBP/USD') is True


def test_get_daily_pl_includes_only_todays_closed_trades():
    today_trade = {
        'status': 'closed', 'exit_time': datetime.now().isoformat(), 'pl_amount': 100,
    }
    yesterday_trade = {
        'status': 'closed',
        'exit_time': (datetime.now() - timedelta(days=1)).isoformat(),
        'pl_amount': 999,
    }
    open_trade = {'status': 'open', 'exit_time': None, 'pl_amount': None}

    pm = make_position_manager(history=[today_trade, yesterday_trade, open_trade])
    agent = ForexRiskAgent(position_manager=pm)

    assert agent.get_daily_pl() == 100


def test_get_daily_pl_adds_unrealized_pl_from_open_positions():
    pm = make_position_manager(positions=[{'pair': 'AAPL', 'unrealized_pl': 50}], history=[])
    agent = ForexRiskAgent(position_manager=pm)

    assert agent.get_daily_pl() == 50
