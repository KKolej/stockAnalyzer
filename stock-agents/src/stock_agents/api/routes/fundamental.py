from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...agents.fundamental.agent import get_data
from ..serializer import to_json

router = APIRouter(prefix="/fundamental", tags=["fundamental"])


@router.get("/{ticker}")
async def fundamental(ticker: str):
    data, signals = get_data(ticker)
    return JSONResponse(content=to_json({"data": data, "signals": signals}))
