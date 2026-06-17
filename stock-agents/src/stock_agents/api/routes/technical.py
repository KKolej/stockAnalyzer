from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ...agents.technical.agent import get_data
from ..serializer import to_json

router = APIRouter(prefix="/technical", tags=["technical"])


@router.get("/{ticker}")
async def technical(ticker: str, days: int = Query(default=90, ge=10, le=1000)) -> JSONResponse:
    data = get_data(ticker, days)
    return JSONResponse(content=to_json(data))
