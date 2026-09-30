"""
Tests for AlpacaPositionManager: position sizing, open/close bookkeeping,
P&L calculation, and position formatting - all against a mocked Alpaca client
so no real network calls are made.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.utils.alpaca_position_manager import AlpacaPositionManager


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.is_configured = True
    client.get_account_info.return_value = {"equity": 10000.0}
    client.get_positions.return_value = []
    client.get_current_price.return_value = None
    return client


@pytest.fixture
def position_manager(tmp_path, mock_client):
    with patch('src.utils.alpaca_position_manager.AlpacaClient', return_value=mock_client):
        pm = AlpacaPositionManager(data_dir=str(tmp_path))
    return pm


def test_calculate_position_size_uses_real_account_equity(position_manager):
    # risk_amount = 10000 * 0.02 = 200; stop_distance = 0.005/0.0001 = 50 pips
    # position_size = (200 / 50) * 100 = 400
    size = position_manager.calculate_position_size('EUR/USD', 1.1000, 1.0950)
    assert size == 400


def test_calculate_position_size_falls_back_when_not_configured(tmp_path):
    client = MagicMock()
    client.is_configured = False
    with patch('src.utils.alpaca_position_manager.AlpacaClient', return_value=client):
        pm = AlpacaPositionManager(data_dir=str(tmp_path))
    # Falls back to simulated $10,000 balance, same math as above
    size = pm.calculate_position_size('EUR/USD', 1.1000, 1.0950)
    assert size == 400


def test_calculate_position_size_zero_stop_distance_returns_zero(position_manager):
    size = position_manager.calculate_position_size('EUR/USD', 1.1000, 1.1000)
    assert size == 0


def test_open_position_records_history_entry(position_manager, tmp_path):
    record = position_manager.open_position('EUR/USD', 'buy', 1.1000, 1000, 1.0950, 1.1100)
    assert record['pair'] == 'EUR/USD'
    assert record['status'] == 'open'

    history_file = tmp_path / 'trade_history.json'
    assert history_file.exists()
    saved = json.loads(history_file.read_text())
    assert len(saved) == 1


def test_close_position_calculates_pl_for_long(position_manager):
    position_manager.open_position('EUR/USD', 'buy', 1.1000, 1000, 1.0950, 1.1100)
    closed = position_manager.close_position('EUR/USD', exit_price=1.1050)

    assert closed['status'] == 'closed'
    # pips = (1.1050 - 1.1000) / 0.0001 = 50; pl = 50 * 1000 = 50000
    assert closed['pips'] == pytest.approx(50)
    assert closed['pl_amount'] == pytest.approx(50000)


def test_close_position_calculates_pl_for_short(position_manager):
    position_manager.open_position('EUR/USD', 'sell', 1.1000, 1000, 1.1050, 1.0900)
    closed = position_manager.close_position('EUR/USD', exit_price=1.0950)

    # pips = (1.1000 - 1.0950) / 0.0001 = 50
    assert closed['pips'] == pytest.approx(50)
    assert closed['pl_amount'] == pytest.approx(50000)


def test_close_position_with_no_open_record_returns_none(position_manager):
    assert position_manager.close_position('GBP/USD') is None


def test_get_positions_formats_alpaca_response(position_manager, mock_client):
    mock_client.get_positions.return_value = [{
        'symbol': 'AAPL',
        'side': 'long',
        'avg_entry_price': 150.0,
        'qty': 10,
        'unrealized_pl': 25.0,
        'market_value': 1525.0,
        'current_price': 152.5,
    }]

    positions = position_manager.get_positions()

    assert len(positions) == 1
    assert positions[0]['pair'] == 'AAPL'
    assert positions[0]['direction'] == 'buy'
    assert positions[0]['entry_price'] == 150.0


def test_get_positions_returns_empty_when_not_configured(tmp_path):
    client = MagicMock()
    client.is_configured = False
    with patch('src.utils.alpaca_position_manager.AlpacaClient', return_value=client):
        pm = AlpacaPositionManager(data_dir=str(tmp_path))
    assert pm.get_positions() == []
