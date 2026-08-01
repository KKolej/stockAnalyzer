"""Alpaca broker client (REST) — account state and order execution.

Defaults to **paper** mode (demo account, no real money). Credentials come
from ENV only (never from code or logs):
    ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_PAPER (1=demo by default, 0=live)

Alpaca: REST, US equities/crypto, free paper accounts. Docs: alpaca.markets/docs
"""
from __future__ import annotations

import contextlib
import json
import os
import urllib.error
import urllib.request
from typing import Any

PAPER_BASE = "https://paper-api.alpaca.markets"
LIVE_BASE = "https://api.alpaca.markets"


class BrokerError(Exception):
    """Broker communication failure (missing credentials, HTTP, network)."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def is_paper() -> bool:
    return os.getenv("ALPACA_PAPER", "1") != "0"


def base_url() -> str:
    return PAPER_BASE if is_paper() else LIVE_BASE


def _credentials() -> tuple[str, str]:
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_API_SECRET")
    if not key or not secret:
        raise BrokerError(
            "Brak danych logowania — ustaw ALPACA_API_KEY i ALPACA_API_SECRET w .env",
            status=503,
        )
    return key, secret


def _request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    key, secret = _credentials()
    url = f"{base_url()}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("APCA-API-KEY-ID", key)
    req.add_header("APCA-API-SECRET-KEY", secret)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        with contextlib.suppress(Exception):
            detail = json.loads(detail).get("message", detail)
        raise BrokerError(f"Alpaca {e.code}: {detail}", status=e.code) from e
    except urllib.error.URLError as e:
        raise BrokerError(f"Błąd połączenia z brokerem: {e.reason}", status=502) from e


# ── Stan konta ───────────────────────────────────────────────────────────────
def get_account() -> dict[str, Any]:
    acc: dict[str, Any] = _request("GET", "/v2/account")
    acc["mode"] = "paper" if is_paper() else "live"
    return acc


def get_positions() -> list[dict[str, Any]]:
    return _request("GET", "/v2/positions") or []


def get_position(symbol: str) -> dict[str, Any]:
    pos: dict[str, Any] = _request("GET", f"/v2/positions/{symbol.upper()}")
    return pos


def get_orders(status: str = "open", limit: int = 50) -> list[dict[str, Any]]:
    return _request("GET", f"/v2/orders?status={status}&limit={limit}") or []


# ── Egzekucja ────────────────────────────────────────────────────────────────
def place_order(
    symbol: str,
    side: str,
    qty: float | None = None,
    notional: float | None = None,
    order_type: str = "market",
    time_in_force: str = "day",
    limit_price: float | None = None,
    stop_price: float | None = None,
) -> dict[str, Any]:
    """Places an order. Pass `qty` (share count) OR `notional` (USD amount)."""
    if qty is None and notional is None:
        raise BrokerError("Podaj qty (liczba akcji) lub notional (kwota USD)", status=400)
    body: dict[str, Any] = {
        "symbol": symbol.upper(),
        "side": side,
        "type": order_type,
        "time_in_force": time_in_force,
    }
    if qty is not None:
        body["qty"] = str(qty)
    if notional is not None:
        body["notional"] = str(notional)
    if limit_price is not None:
        body["limit_price"] = str(limit_price)
    if stop_price is not None:
        body["stop_price"] = str(stop_price)
    order: dict[str, Any] = _request("POST", "/v2/orders", body)
    return order


def cancel_order(order_id: str) -> dict[str, Any]:
    _request("DELETE", f"/v2/orders/{order_id}")
    return {"cancelled": order_id}


def close_position(symbol: str) -> dict[str, Any]:
    result: dict[str, Any] = _request("DELETE", f"/v2/positions/{symbol.upper()}")
    return result
