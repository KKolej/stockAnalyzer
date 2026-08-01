from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...agents.broker import client
from ...agents.broker.client import BrokerError
from ..schemas import AccountResponse, Order, OrderRequest, Position

router = APIRouter(prefix="/broker", tags=["broker"])


def _guard(fn: Any) -> Any:
    """Turns a BrokerError into a clean HTTP error instead of a 500."""
    try:
        return fn()
    except BrokerError as e:
        raise HTTPException(status_code=e.status or 502, detail=str(e)) from e


@router.get("/account", response_model=AccountResponse)
def account() -> Any:
    """Account state: balance, equity, buying power, mode (paper/live)."""
    return _guard(client.get_account)


@router.get("/positions", response_model=list[Position])
def positions() -> Any:
    """Otwarte pozycje."""
    return _guard(client.get_positions)


@router.get("/orders", response_model=list[Order])
def orders(status: str = Query(default="open", description="open|closed|all")) -> Any:
    """Orders (open ones by default)."""
    return _guard(lambda: client.get_orders(status))


@router.post("/orders", response_model=Order)
def submit_order(req: OrderRequest) -> Any:
    """Places a buy/sell order (paper = demo)."""
    return _guard(lambda: client.place_order(
        symbol=req.symbol,
        side=req.side,
        qty=req.qty,
        notional=req.notional,
        order_type=req.order_type,
        time_in_force=req.time_in_force,
        limit_price=req.limit_price,
        stop_price=req.stop_price,
    ))


@router.delete("/orders/{order_id}")
def cancel(order_id: str) -> Any:
    """Anuluje otwarte zlecenie."""
    return _guard(lambda: client.cancel_order(order_id))


@router.delete("/positions/{symbol}", response_model=Order)
def close(symbol: str) -> Any:
    """Closes the whole position on a given symbol (opposite order)."""
    return _guard(lambda: client.close_position(symbol))
