from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ...agents.sentiment.agent import get_data
from ...agents.sentiment.models import AnalysisMode
from ..serializer import to_json

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{ticker}")
async def sentiment(
    ticker: str,
    mode: str = Query(default="keyword", description="keyword|claude"),
) -> JSONResponse:
    m = AnalysisMode.CLAUDE if mode == "claude" else AnalysisMode.KEYWORD
    data = get_data(ticker, m)
    return JSONResponse(content=to_json(data))
