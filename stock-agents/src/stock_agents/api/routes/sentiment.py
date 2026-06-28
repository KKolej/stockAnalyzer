from __future__ import annotations

from fastapi import APIRouter, Query

from ...agents.sentiment.agent import get_data
from ...agents.sentiment.models import AnalysisMode
from ..schemas import SentimentResponse
from ..serializer import to_json

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{ticker}", response_model=SentimentResponse)
async def sentiment(
    ticker: str,
    mode: str = Query(default="keyword", description="keyword|claude"),
) -> SentimentResponse:
    m = AnalysisMode.CLAUDE if mode == "claude" else AnalysisMode.KEYWORD
    data = get_data(ticker, m)
    return SentimentResponse.model_validate(to_json(data))
