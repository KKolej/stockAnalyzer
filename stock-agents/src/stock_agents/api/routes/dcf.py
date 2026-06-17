from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ...agents.dcf.fetcher import fetch
from ..serializer import to_json

router = APIRouter(prefix="/dcf", tags=["dcf"])


@router.get("/{ticker}")
async def dcf(ticker: str, years: int = Query(default=10, ge=3, le=20)) -> JSONResponse:
    data = fetch(ticker, years)
    return JSONResponse(content=to_json(data))
