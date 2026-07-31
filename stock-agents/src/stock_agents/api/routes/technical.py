from __future__ import annotations

from fastapi import APIRouter, Query

from ...agents.technical.agent import get_data
from ..schemas import TechnicalResponse
from ..serializer import to_json

router = APIRouter(prefix="/technical", tags=["technical"])


@router.get("/{ticker}", response_model=TechnicalResponse)
def technical(ticker: str, days: int = Query(default=90, ge=10, le=1000)) -> TechnicalResponse:
    data = get_data(ticker, days)
    return TechnicalResponse.model_validate(to_json(data))
