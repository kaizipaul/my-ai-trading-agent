"""
Tests for src.config.validate_config(): the startup guard that refuses to
run with EXECUTE_TRADES=true unless Alpaca credentials are present, and
refuses a live (real-money) endpoint without an explicit opt-in.
"""
import pytest

import src.config as config


def test_validate_config_passes_with_default_settings(monkeypatch):
    monkeypatch.setattr(config, 'EXECUTE_TRADES', False)
    config.validate_config()  # should not raise


def test_validate_config_blocks_execute_trades_without_credentials(monkeypatch):
    monkeypatch.setattr(config, 'EXECUTE_TRADES', True)
    monkeypatch.setattr(config, 'ALPACA_API_KEY', '')
    monkeypatch.setattr(config, 'ALPACA_API_SECRET', '')
    monkeypatch.setattr(config, 'ALPACA_API_URL', 'https://paper-api.alpaca.markets')

    with pytest.raises(config.ConfigError):
        config.validate_config()


def test_validate_config_blocks_live_endpoint_without_opt_in(monkeypatch):
    monkeypatch.setattr(config, 'EXECUTE_TRADES', True)
    monkeypatch.setattr(config, 'ALPACA_API_KEY', 'key')
    monkeypatch.setattr(config, 'ALPACA_API_SECRET', 'secret')
    monkeypatch.setattr(config, 'ALPACA_API_URL', 'https://api.alpaca.markets')
    monkeypatch.delenv('ALLOW_LIVE_TRADING', raising=False)

    with pytest.raises(config.ConfigError):
        config.validate_config()


def test_validate_config_allows_live_endpoint_with_explicit_opt_in(monkeypatch):
    monkeypatch.setattr(config, 'EXECUTE_TRADES', True)
    monkeypatch.setattr(config, 'ALPACA_API_KEY', 'key')
    monkeypatch.setattr(config, 'ALPACA_API_SECRET', 'secret')
    monkeypatch.setattr(config, 'ALPACA_API_URL', 'https://api.alpaca.markets')
    monkeypatch.setenv('ALLOW_LIVE_TRADING', 'true')

    config.validate_config()  # should not raise


def test_validate_config_allows_paper_endpoint_with_credentials(monkeypatch):
    monkeypatch.setattr(config, 'EXECUTE_TRADES', True)
    monkeypatch.setattr(config, 'ALPACA_API_KEY', 'key')
    monkeypatch.setattr(config, 'ALPACA_API_SECRET', 'secret')
    monkeypatch.setattr(config, 'ALPACA_API_URL', 'https://paper-api.alpaca.markets')

    config.validate_config()  # should not raise


def test_validate_config_rejects_invalid_risk_per_trade(monkeypatch):
    monkeypatch.setattr(config, 'EXECUTE_TRADES', False)
    monkeypatch.setattr(config, 'MAX_POSITION_SIZE', 1.5)

    with pytest.raises(config.ConfigError):
        config.validate_config()


def test_validate_config_rejects_empty_symbols(monkeypatch):
    monkeypatch.setattr(config, 'EXECUTE_TRADES', False)
    monkeypatch.setattr(config, 'FOREX_PAIRS', [])

    with pytest.raises(config.ConfigError):
        config.validate_config()
