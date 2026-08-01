from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import (
    analyze,
    broker,
    compare,
    dcf,
    fundamental,
    macro,
    screener,
    sentiment,
    speculator,
    technical,
)

app = FastAPI(
    title="Stock Agents API",
    description="REST API dla agentów analizy giełdowej — GPW i rynki zagraniczne",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(technical.router)
app.include_router(fundamental.router)
app.include_router(screener.router)
app.include_router(speculator.router)
app.include_router(sentiment.router)
app.include_router(dcf.router)
app.include_router(compare.router)
app.include_router(macro.router)
app.include_router(analyze.router)
app.include_router(broker.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
async def version() -> dict[str, str]:
    """Wersja wdrożonego kodu — pozwala wykryć, że kontener chodzi na starym obrazie.

    Powód: przez ~dobę obraz w Dockerze był starszy niż repo i sentyment z Google
    News zwracał zero artykułów dla WSZYSTKICH spółek, a nikt tego nie zauważył,
    bo /health nadal mówiło "ok".
    """
    return {
        "git_sha": os.getenv("GIT_SHA", "unknown"),
        "built_at": os.getenv("BUILD_TIME", "unknown"),
        "api_version": app.version,
    }


@app.get("/")
async def index() -> dict[str, dict[str, str]]:
    return {
        "endpoints": {
            "GET /health": "ping",
            "GET /version": "git SHA + czas budowy obrazu (kontrola świeżości wdrożenia)",
            "GET /technical/{ticker}": "analiza techniczna, ?days=90",
            "GET /fundamental/{ticker}": "analiza fundamentalna",
            "GET /screener": "screener, ?tickers=CDR,PKO&pe_max=20&sort_by=pe",
            "GET /speculator/{ticker}": "wzorce, katalyzatory, projekcje",
            "GET /sentiment/{ticker}": "sentyment mediów, ?mode=keyword|claude",
            "GET /dcf/{ticker}": "wycena DCF, ?years=10",
            "GET /compare": "porównanie, ?tickers=CDR,PKO,KGHM",
            "GET /macro": "dane makro GPW (kursy walut, WIG20, sektory)",
            "GET /analyze/{ticker}": "ZBIORCZA analiza — wszyscy agenci + werdykt",
            "GET /broker/account": "stan konta Alpaca (paper/demo)",
            "GET /broker/positions": "otwarte pozycje",
            "POST /broker/orders": "złóż zlecenie (paper)",
        }
    }
