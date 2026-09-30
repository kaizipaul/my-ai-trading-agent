"""
Tests for the call_with_retry helper used to add backoff to read-only
Alpaca API calls.
"""
import pytest

from src.utils import call_with_retry


def test_call_with_retry_succeeds_after_transient_failures(monkeypatch):
    monkeypatch.setattr('src.utils.time.sleep', lambda s: None)
    calls = {'count': 0}

    def flaky():
        calls['count'] += 1
        if calls['count'] < 3:
            raise ConnectionError('transient')
        return 'ok'

    result = call_with_retry(flaky, max_attempts=3, base_delay=0.01)

    assert result == 'ok'
    assert calls['count'] == 3


def test_call_with_retry_raises_after_exhausting_attempts(monkeypatch):
    monkeypatch.setattr('src.utils.time.sleep', lambda s: None)

    def always_fails():
        raise ConnectionError('down')

    with pytest.raises(ConnectionError):
        call_with_retry(always_fails, max_attempts=2, base_delay=0.01)


def test_call_with_retry_passes_args_and_kwargs(monkeypatch):
    monkeypatch.setattr('src.utils.time.sleep', lambda s: None)

    def add(a, b, c=0):
        return a + b + c

    assert call_with_retry(add, 1, 2, c=3) == 6


def test_call_with_retry_succeeds_first_try_without_sleeping(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr('src.utils.time.sleep', lambda s: sleep_calls.append(s))

    result = call_with_retry(lambda: 'immediate')

    assert result == 'immediate'
    assert sleep_calls == []
