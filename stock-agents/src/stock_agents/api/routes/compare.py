from __future__ import annotations

import concurrent.futures

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ...agents.compare.agent import _fetch_one
from ..schemas import CompareResponse
from ..serializer import to_json

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("", response_model=CompareResponse)
async def compare(
    tickers: str = Query(description="Tickery oddzielone przecinkiem, np. CDR,PKO,KGHM"),
) -> CompareResponse | JSONResponse:
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(ticker_list) < 2:
        return JSONResponse(status_code=400, content={"error": "Podaj co najmniej 2 tickery"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_one, t): t for t in ticker_list}
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    order = {t.upper(): i for i, t in enumerate(ticker_list)}
    results.sort(key=lambda r: order.get(r["ticker"], 999))
    return CompareResponse.model_validate(to_json({"tickers": ticker_list, "data": results}))
