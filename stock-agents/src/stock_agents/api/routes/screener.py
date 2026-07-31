from __future__ import annotations

from fastapi import APIRouter, Query

from ...agents.screener.agent import get_data
from ...agents.screener.models import ScreenerFilters
from ..schemas import ScreenerResponse
from ..serializer import to_json

router = APIRouter(prefix="/screener", tags=["screener"])

# Domyślne tickery GPW
_DEFAULT_TICKERS = [
    "PKO", "CDR", "KGHM", "PZU", "PKN", "LPP", "ALE", "DNP",
    "MBK", "OPL", "CPS", "JSW", "CCC", "BDX", "TPE", "PGE",
]


@router.get("", response_model=ScreenerResponse)
def screener(
    tickers: str = Query(default=",".join(_DEFAULT_TICKERS), description="Tickery oddzielone przecinkiem"),
    pe_max: float | None = None,
    pe_min: float | None = None,
    pb_max: float | None = None,
    roe_min: float | None = None,
    margin_min: float | None = None,
    div_min: float | None = None,
    ic_min: float | None = None,
    market_cap_min: float | None = None,
    market_cap_max: float | None = None,
    debt_max: float | None = None,
    sort_by: str = Query(default="pe", description="pe|pb|roe|margin|div|ic|cap"),
    top: int | None = Query(default=None, ge=1, le=50),
    magic_formula: bool = False,
) -> ScreenerResponse:
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    filters = ScreenerFilters(
        pe_max=pe_max, pe_min=pe_min, pb_max=pb_max,
        roe_min=roe_min, margin_min=margin_min, div_min=div_min,
        ic_min=ic_min, market_cap_min=market_cap_min, market_cap_max=market_cap_max,
        debt_max=debt_max, sort_by=sort_by, top=top, magic_formula=magic_formula,
    )
    all_rows, filtered = get_data(ticker_list, filters)
    return ScreenerResponse.model_validate(to_json({
        "total": len(all_rows),
        "matched": len(filtered),
        "filters": filters,
        "rows": filtered,
        "errors": [r for r in all_rows if r.error],
    }))
