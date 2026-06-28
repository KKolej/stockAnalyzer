from __future__ import annotations

from fastapi import APIRouter, Query

from ...agents.dcf.fetcher import fetch
from ..schemas import DCFResponse
from ..serializer import to_json

router = APIRouter(prefix="/dcf", tags=["dcf"])


@router.get("/{ticker}", response_model=DCFResponse)
async def dcf(ticker: str, years: int = Query(default=10, ge=3, le=20)) -> DCFResponse:
    data = fetch(ticker, years)
    return DCFResponse.model_validate(to_json(data))
