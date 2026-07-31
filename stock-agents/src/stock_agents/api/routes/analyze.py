from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ...agents.aggregate import analyze
from ...agents.sentiment.models import AnalysisMode
from ..serializer import to_json

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.get("/{ticker}")
def analyze_ticker(
    ticker: str,
    days: int = Query(default=180, ge=30, le=1000),
    sentiment_mode: str = Query(default="keyword", description="keyword|claude"),
) -> JSONResponse:
    mode = AnalysisMode.CLAUDE if sentiment_mode == "claude" else AnalysisMode.KEYWORD
    data = analyze(ticker, days, mode)
    return JSONResponse(content=to_json(data))
