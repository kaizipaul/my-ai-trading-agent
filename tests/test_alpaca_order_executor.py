"""
Tests for AlpacaOrderExecutor: simulation-mode fallback and the response
mapping around a (mocked) Alpaca client. No real network calls are made.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.utils.alpaca_order_executor import AlpacaOrderExecutor


def _make_executor(monkeypatch, environment, is_configured, client_overrides=None):
    monkeypatch.setenv('ENVIRONMENT', environment)
    with patch('src.utils.alpaca_order_executor.AlpacaClient') as MockClient:
        mock_client = MockClient.return_value
        mock_client.is_configured = is_configured
        for attr, value in (client_overrides or {}).items():
            getattr(mock_client, attr).return_value = value
        executor = AlpacaOrderExecutor()
        return executor, mock_client


def test_place_market_order_simulated_when_unconfigured_in_dev(monkeypatch):
    executor, mock_client = _make_executor(monkeypatch, 'development', is_configured=False)

    result = executor.place_market_order('AAPL', 'buy', 10)

    assert result['status'] == 'FILLED'
    assert result['orderId'].startswith('sim-')
    mock_client.place_market_order.assert_not_called()


def test_close_trade_simulated_when_unconfigured_in_dev(monkeypatch):
    executor, mock_client = _make_executor(monkeypatch, 'development', is_configured=False)

    result = executor.close_trade('AAPL')

    assert result['status'] == 'CLOSED'
    mock_client.close_position.assert_not_called()


def test_close_all_positions_simulated_when_unconfigured_in_dev(monkeypatch):
    executor, mock_client = _make_executor(monkeypatch, 'development', is_configured=False)

    result = executor.close_all_positions()

    assert result['status'] == 'CLOSED_ALL'
    mock_client.close_all_positions.assert_not_called()


def test_place_market_order_success_maps_alpaca_response(monkeypatch):
    executor, mock_client = _make_executor(
        monkeypatch, 'production', is_configured=True,
        client_overrides={'place_market_order': {
            'order_id': 'abc123', 'symbol': 'AAPL', 'side': 'buy', 'qty': 10, 'status': 'filled'
        }}
    )

    result = executor.place_market_order('AAPL', 'buy', 10, stop_loss=140, take_profit=160)

    assert result['orderId'] == 'abc123'
    assert result['status'] == 'filled'
    mock_client.place_market_order.assert_called_once()


def test_place_market_order_failure_returns_none(monkeypatch):
    executor, mock_client = _make_executor(
        monkeypatch, 'production', is_configured=True,
        client_overrides={'place_market_order': {'error': 'insufficient buying power'}}
    )

    result = executor.place_market_order('AAPL', 'buy', 10)

    assert result is None


def test_close_trade_failure_returns_none(monkeypatch):
    executor, mock_client = _make_executor(
        monkeypatch, 'production', is_configured=True,
        client_overrides={'close_position': {'error': 'no position'}}
    )

    result = executor.close_trade('AAPL')

    assert result is None


def test_get_account_info_simulated_when_unconfigured_in_dev(monkeypatch):
    executor, mock_client = _make_executor(monkeypatch, 'development', is_configured=False)

    info = executor.get_account_info()

    assert info['account_id'] == 'simulated-account'
    assert info['equity'] == 100000.0
