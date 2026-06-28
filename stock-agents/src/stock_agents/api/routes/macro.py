from __future__ import annotations

from fastapi import APIRouter

from ...agents.macro.agent import get_data
from ..schemas import MacroResponse
from ..serializer import to_json

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("", response_model=MacroResponse)
async def macro() -> MacroResponse:
    data = get_data()
    return MacroResponse.model_validate(to_json(data))
