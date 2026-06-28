import pytest

from stock_agents.agents.broker import client
from stock_agents.agents.broker.client import BrokerError


def test_is_paper_default_true(monkeypatch):
    monkeypatch.delenv("ALPACA_PAPER", raising=False)
    assert client.is_paper() is True
    assert client.base_url() == client.PAPER_BASE


def test_live_mode_when_paper_zero(monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER", "0")
    assert client.is_paper() is False
    assert client.base_url() == client.LIVE_BASE


def test_missing_credentials_raises_503(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    with pytest.raises(BrokerError) as exc:
        client.get_account()
    assert exc.value.status == 503


def test_get_account_adds_mode(monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER", "1")
    monkeypatch.setattr(client, "_request", lambda *a, **k: {"cash": "1000"})
    acc = client.get_account()
    assert acc["mode"] == "paper"
    assert acc["cash"] == "1000"


def test_place_order_requires_qty_or_notional(monkeypatch):
    monkeypatch.setattr(client, "_request", lambda *a, **k: {})
    with pytest.raises(BrokerError) as exc:
        client.place_order("AAPL", "buy")
    assert exc.value.status == 400


def test_place_order_builds_body(monkeypatch):
    captured = {}

    def fake(method, path, body=None):
        captured["method"] = method
        captured["path"] = path
        captured["body"] = body
        return {"id": "abc", "status": "accepted"}

    monkeypatch.setattr(client, "_request", fake)
    out = client.place_order("aapl", "buy", qty=3, limit_price=150.5, order_type="limit")
    assert out["id"] == "abc"
    assert captured["method"] == "POST"
    assert captured["path"] == "/v2/orders"
    assert captured["body"]["symbol"] == "AAPL"  # upper
    assert captured["body"]["qty"] == "3"
    assert captured["body"]["limit_price"] == "150.5"
    assert "notional" not in captured["body"]


def test_get_positions_handles_empty(monkeypatch):
    monkeypatch.setattr(client, "_request", lambda *a, **k: None)
    assert client.get_positions() == []
