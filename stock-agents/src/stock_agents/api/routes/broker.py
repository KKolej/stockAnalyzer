from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...agents.broker import client
from ...agents.broker.client import BrokerError
from ..schemas import AccountResponse, Order, OrderRequest, Position

router = APIRouter(prefix="/broker", tags=["broker"])


def _guard(fn: Any) -> Any:
    """Zamienia BrokerError na czysty błąd HTTP zamiast 500."""
    try:
        return fn()
    except BrokerError as e:
        raise HTTPException(status_code=e.status or 502, detail=str(e)) from e


@router.get("/account", response_model=AccountResponse)
def account() -> Any:
    """Stan konta: saldo, equity, siła nabywcza, tryb (paper/live)."""
    return _guard(client.get_account)


@router.get("/positions", response_model=list[Position])
def positions() -> Any:
    """Otwarte pozycje."""
    return _guard(client.get_positions)


@router.get("/orders", response_model=list[Order])
def orders(status: str = Query(default="open", description="open|closed|all")) -> Any:
    """Zlecenia (domyślnie otwarte)."""
    return _guard(lambda: client.get_orders(status))


@router.post("/orders", response_model=Order)
def submit_order(req: OrderRequest) -> Any:
    """Składa zlecenie kupna/sprzedaży (paper = demo)."""
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
    """Zamyka całą pozycję na danym symbolu (zlecenie przeciwne)."""
    return _guard(lambda: client.close_position(symbol))
