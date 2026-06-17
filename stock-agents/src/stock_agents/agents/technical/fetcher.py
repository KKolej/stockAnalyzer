import pandas as pd
import yfinance as yf

from ...cache import ttl_cache
from ...ticker_map import is_gpw, to_yahoo_ticker

REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}

# Benchmarki do liczenia bety (rynek systematyczny).
# WIG20.WA w yfinance daje tylko 1 dzień historii, więc dla GPW używamy EWP
# (iShares MSCI Poland ETF, notowany w USA) jako proxy rynku polskiego.
BENCHMARK_GPW = "EWP"
BENCHMARK_US = "^GSPC"
_BENCHMARK_NAMES = {"EWP": "EWP (proxy GPW)", "^GSPC": "S&P 500"}


class FetchError(Exception):
    pass


def benchmark_symbol(ticker: str) -> str:
    return BENCHMARK_GPW if is_gpw(ticker) else BENCHMARK_US


def benchmark_name(ticker: str) -> str:
    sym = benchmark_symbol(ticker)
    return _BENCHMARK_NAMES.get(sym, sym)


@ttl_cache()
def download_ohlcv(yahoo_ticker: str, ticker: str, days_back: int) -> pd.DataFrame:
    period = f"{days_back}d"
    df: pd.DataFrame = yf.download(
        yahoo_ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if df.empty:
        raise FetchError(
            f"Brak danych dla '{ticker}' (Yahoo Finance: {yahoo_ticker}). "
            f"Sprawdź poprawność symbolu."
        )
    return df


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(level=1, axis=1)
    return df


def normalize_ohlcv(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    df = flatten_columns(df).copy()
    df.index.name = "Date"
    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Close"])
    return df.sort_values("Date").reset_index(drop=True)


def validate_columns(df: pd.DataFrame, ticker: str) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise FetchError(f"Nieoczekiwany format danych dla '{ticker}' — brak kolumn: {missing}.")


def fetch_ohlcv(ticker: str, days_back: int = 90) -> pd.DataFrame:
    yahoo_ticker = to_yahoo_ticker(ticker)
    raw = download_ohlcv(yahoo_ticker, ticker, days_back)
    df = normalize_ohlcv(raw, ticker)
    validate_columns(df, ticker)
    return df


@ttl_cache()
def _download_close(yahoo_symbol: str, days_back: int) -> pd.DataFrame:
    df: pd.DataFrame = yf.download(yahoo_symbol, period=f"{days_back}d", interval="1d",
                                   auto_adjust=True, progress=False)
    return df


def fetch_close_series(yahoo_symbol: str, days_back: int = 90) -> pd.Series | None:
    """Pobiera samą serię Close dla dowolnego symbolu Yahoo (np. indeksu/benchmarku)."""
    try:
        df = _download_close(yahoo_symbol, days_back)
        if df is None or df.empty:
            return None
        df = flatten_columns(df)
        return pd.to_numeric(df["Close"], errors="coerce").dropna()
    except Exception:
        return None


def data_staleness(df: pd.DataFrame) -> dict[str, object]:
    """Sprawdza, jak świeża jest ostatnia świeca (yfinance bywa opóźniony/stale)."""
    last_date = pd.to_datetime(df["Date"].iloc[-1]).normalize()
    today = pd.Timestamp.now().normalize()
    age_days = int((today - last_date).days)
    # >4 dni kalendarzowych = podejrzanie nieświeże (uwzględnia weekend + święto)
    return {
        "last_date": last_date.strftime("%Y-%m-%d"),
        "age_days": age_days,
        "is_stale": age_days > 4,
    }
