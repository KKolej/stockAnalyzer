from __future__ import annotations

from fastapi import APIRouter

from ...agents.fundamental.agent import get_data
from ..schemas import FundamentalResponse
from ..serializer import to_json

router = APIRouter(prefix="/fundamental", tags=["fundamental"])


@router.get("/{ticker}", response_model=FundamentalResponse)
async def fundamental(ticker: str) -> FundamentalResponse:
    data, signals = get_data(ticker)
    return FundamentalResponse.model_validate(to_json({"data": data, "signals": signals}))
