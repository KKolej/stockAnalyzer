from __future__ import annotations

from fastapi import APIRouter, Query

from ...agents.backtest.agent import get_data
from ..schemas import BacktestResponse
from ..serializer import to_json

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.get(
    "/{ticker}",
    response_model=BacktestResponse,
    summary="Measured track record of technical signals on this ticker",
    description=(
        "For every signal (RSI crossing 30, MACD cross, new 52-week high, ...) returns what "
        "actually happened afterwards on this stock's own history: hit rate against the "
        "baseline of holding, excess return, sample size and a significance test. "
        "Answers 'which signals to trust here', never 'what the price will be'."
    ),
)
def backtest(
    ticker: str,
    years: int = Query(default=5, ge=2, le=20, description="How much history to test"),
) -> BacktestResponse:
    data = get_data(ticker, years)
    return BacktestResponse.model_validate(to_json(data))
