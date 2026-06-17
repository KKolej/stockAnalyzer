from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...agents.macro.agent import get_data
from ..serializer import to_json

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("")
async def macro():
    data = get_data()
    return JSONResponse(content=to_json(data))
