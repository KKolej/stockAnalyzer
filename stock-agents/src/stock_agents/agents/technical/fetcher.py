import pandas as pd
import yfinance as yf

from ...cache import ttl_cache
from ...ticker_map import is_gpw, to_yahoo_ticker

REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}

# Benchmarks for beta (systematic market risk).
# WIG20.WA gives only 1 day of history in yfinance, so for GPW we use EWP
# (iShares MSCI Poland ETF, listed in the US) as a proxy for the Polish market.
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
    """Fetches just the Close series for any Yahoo symbol (e.g. an index/benchmark)."""
    try:
        df = _download_close(yahoo_symbol, days_back)
        if df is None or df.empty:
            return None
        df = flatten_columns(df)
        return pd.to_numeric(df["Close"], errors="coerce").dropna()
    except Exception:
        return None


def _last_expected_session(today: pd.Timestamp) -> pd.Timestamp:
    """Most recent weekday (Mon-Fri) no later than today."""
    day = today
    while day.weekday() >= 5:  # 5=sobota, 6=niedziela
        day -= pd.Timedelta(days=1)
    return day


def data_staleness(df: pd.DataFrame) -> dict[str, object]:
    """Checks how fresh the last candle is (yfinance is often delayed or stale).

    Counts MISSING SESSIONS, not calendar days. Age in days alone is not enough:
    on a Saturday a missing Friday session gives age_days=2, so the old threshold
    (>4 days) let it through and the whole analysis ran on data one session old
    without a warning. Non-trading days (holidays) may raise a false alarm — which
    is why we publish the session count and the date next to the flag, so the
    consumer can judge for themselves.
    """
    last_date = pd.to_datetime(df["Date"].iloc[-1]).normalize()
    today = pd.Timestamp.now().normalize()
    age_days = int((today - last_date).days)

    expected = _last_expected_session(today)
    missing = int(len(pd.bdate_range(last_date, expected))) - 1
    missing_sessions = max(missing, 0)

    return {
        "last_date": last_date.strftime("%Y-%m-%d"),
        "age_days": age_days,
        "expected_last_session": expected.strftime("%Y-%m-%d"),
        "missing_sessions": missing_sessions,
        "is_stale": age_days > 4 or missing_sessions >= 1,
    }
