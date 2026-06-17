from __future__ import annotations

import pandas as pd

from stock_agents.agents.technical.fetcher import FetchError, fetch_ohlcv
from stock_agents.agents.technical.indicators import add_all_indicators
from stock_agents.agents.technical.printer import print_ticker_analysis
from stock_agents.agents.technical.signals import generate_signals


def get_data(ticker: str, days_back: int = 90) -> dict:
    try:
        df = fetch_ohlcv(ticker, max(days_back, 90))
        df = add_all_indicators(df)
        signals = generate_signals(df)
        last = df.iloc[-1]

        def _val(col: str) -> float | None:
            v = last.get(col)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            try:
                return round(float(v), 4)
            except (TypeError, ValueError):
                return None

        score = sum(
            1 if s["signal"] == "BULLISH" else -1
            for s in signals
        )
        return {
            "ticker": ticker.upper(),
            "price": _val("Close"),
            "indicators": {
                "rsi": _val("RSI_14"),
                "macd": _val("MACD"),
                "macd_signal": _val("MACD_signal"),
                "macd_hist": _val("MACD_hist"),
                "sma20": _val("SMA_20"),
                "sma50": _val("SMA_50"),
                "ema20": _val("EMA_20"),
                "ema50": _val("EMA_50"),
                "bb_upper": _val("BB_upper"),
                "bb_lower": _val("BB_lower"),
                "adx": _val("ADX"),
                "stoch_k": _val("STOCH_k"),
                "stoch_d": _val("STOCH_d"),
                "atr": _val("ATR_14"),
                "cmf": _val("CMF"),
                "mfi": _val("MFI_14"),
                "supertrend": _val("Supertrend"),
                "cci": _val("CCI_14"),
            },
            "signals": signals,
            "score": score,
            "error": None,
        }
    except Exception as exc:
        return {"ticker": ticker.upper(), "error": str(exc)}


def analyze_ticker(ticker: str, days_back: int) -> None:
    try:
        df = fetch_ohlcv(ticker, days_back)
        df = add_all_indicators(df)
        signals = generate_signals(df)
        print_ticker_analysis(ticker, df, signals)
    except FetchError as exc:
        print(f"[BŁĄD] {ticker}: {exc}")


def run_technical_agent(tickers: list[str], days_back: int) -> None:
    for ticker in tickers:
        analyze_ticker(ticker, days_back)
