from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...agents.speculator.agent import get_data
from ..serializer import to_json

router = APIRouter(prefix="/speculator", tags=["speculator"])


@router.get("/{ticker}")
async def speculator(ticker: str) -> JSONResponse:
    data = get_data(ticker)
    return JSONResponse(content=to_json(data))
