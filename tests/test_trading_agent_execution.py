"""
Tests for ForexTradingAgent's trade execution path: the risk gate,
same-direction skip, opposite-direction reversal, and the close_all_positions
snapshot-before-close ordering. Uses a real ForexTradingAgent with its
order_executor/position_manager/risk_agent swapped for mocks, so no real
Alpaca or market-data calls happen.
"""
import pytest
from unittest.mock import MagicMock

from src.agents.trading_agent import ForexTradingAgent


@pytest.fixture
def agent(monkeypatch):
    # No Alpaca credentials in the test environment, so construction stays
    # in simulation mode; we still swap in mocks for full control.
    monkeypatch.delenv('ALPACA_API_KEY', raising=False)
    monkeypatch.delenv('ALPACA_API_SECRET', raising=False)

    trading_agent = ForexTradingAgent()
    trading_agent.order_executor = MagicMock()
    trading_agent.position_manager = MagicMock()
    trading_agent.risk_agent = MagicMock()

    trading_agent.risk_agent.check_risk_metrics.return_value = True
    trading_agent.position_manager.get_positions.return_value = []
    trading_agent.order_executor.place_market_order.return_value = {
        'orderId': 'sim-1', 'status': 'FILLED'
    }

    return trading_agent


def make_recommendation(**overrides):
    rec = {
        'symbol': 'EUR/USD',
        'recommendation': 'LONG',
        'entry_price': 1.1000,
        'stop_loss': 1.0950,
        'take_profit': 1.1100,
        'position_size': 1000,
    }
    rec.update(overrides)
    return rec


def test_neutral_recommendation_is_not_executed(agent):
    rec = make_recommendation(recommendation='NEUTRAL')

    result = agent.execute_recommendation(rec)

    assert result is False
    agent.order_executor.place_market_order.assert_not_called()


def test_zero_position_size_is_not_executed(agent):
    rec = make_recommendation(position_size=0)

    result = agent.execute_recommendation(rec)

    assert result is False
    agent.order_executor.place_market_order.assert_not_called()


def test_risk_gate_blocks_execution(agent):
    agent.risk_agent.check_risk_metrics.return_value = False
    rec = make_recommendation()

    result = agent.execute_recommendation(rec)

    assert result is False
    agent.order_executor.place_market_order.assert_not_called()


def test_existing_same_direction_position_is_skipped(agent):
    agent.position_manager.get_positions.return_value = [
        {'pair': 'EUR/USD', 'direction': 'buy'}
    ]
    rec = make_recommendation(recommendation='LONG')

    result = agent.execute_recommendation(rec)

    assert result is False
    agent.order_executor.place_market_order.assert_not_called()


def test_opposite_direction_position_is_closed_then_reversed(agent):
    agent.position_manager.get_positions.return_value = [
        {'pair': 'EUR/USD', 'direction': 'sell'}
    ]
    rec = make_recommendation(recommendation='LONG')

    result = agent.execute_recommendation(rec)

    assert result is True
    agent.order_executor.close_trade.assert_called_once_with('EUR/USD')
    agent.position_manager.close_position.assert_called_once()
    assert agent.position_manager.close_position.call_args.kwargs['reason'] == 'direction_change'
    agent.order_executor.place_market_order.assert_called_once()


def test_successful_order_records_open_position(agent):
    rec = make_recommendation()

    result = agent.execute_recommendation(rec)

    assert result is True
    agent.position_manager.open_position.assert_called_once()


def test_failed_order_does_not_record_open_position(agent):
    agent.order_executor.place_market_order.return_value = None
    rec = make_recommendation()

    result = agent.execute_recommendation(rec)

    assert result is False
    agent.position_manager.open_position.assert_not_called()


def test_close_all_positions_snapshots_before_closing(agent):
    # Positions are fetched exactly once, before the bulk close call - the
    # old code re-fetched afterwards and always saw an empty list, so
    # history was never marked closed for a bulk close.
    agent.position_manager.get_positions.side_effect = [
        [{'pair': 'AAPL'}, {'pair': 'MSFT'}],
    ]
    agent.order_executor.close_all_positions.return_value = {'status': 'CLOSED_ALL'}

    result = agent.close_all_positions()

    assert result is True
    assert agent.position_manager.close_position.call_count == 2
    closed_pairs = [c.args[0] for c in agent.position_manager.close_position.call_args_list]
    assert closed_pairs == ['AAPL', 'MSFT']


def test_close_all_positions_failure_does_not_touch_history(agent):
    agent.position_manager.get_positions.return_value = [{'pair': 'AAPL'}]
    agent.order_executor.close_all_positions.return_value = None

    result = agent.close_all_positions()

    assert result is False
    agent.position_manager.close_position.assert_not_called()
