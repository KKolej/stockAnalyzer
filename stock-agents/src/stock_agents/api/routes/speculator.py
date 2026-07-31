from __future__ import annotations

from fastapi import APIRouter

from ...agents.speculator.agent import get_data
from ..schemas import SpeculatorResponse
from ..serializer import to_json

router = APIRouter(prefix="/speculator", tags=["speculator"])


@router.get("/{ticker}", response_model=SpeculatorResponse)
def speculator(ticker: str) -> SpeculatorResponse:
    data = get_data(ticker)
    return SpeculatorResponse.model_validate(to_json(data))
