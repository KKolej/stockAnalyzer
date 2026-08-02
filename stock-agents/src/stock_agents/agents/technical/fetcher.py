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

# Repairing the newest candle (see `repair_last_session`)
_REPAIR_LOOKBACK_DAYS = 10
_QUOTE_TOLERANCE = 0.005  # the quote may sit marginally outside the reported range


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


@ttl_cache()
def _download_unadjusted(yahoo_ticker: str, days_back: int) -> pd.DataFrame:
    df: pd.DataFrame = yf.download(
        yahoo_ticker,
        period=f"{days_back}d",
        interval="1d",
        auto_adjust=False,
        progress=False,
    )
    return df


@ttl_cache()
def _last_quote(yahoo_ticker: str) -> float | None:
    """Latest price from `fast_info` — the quote yfinance still has when the candle lacks a Close."""
    try:
        price = yf.Ticker(yahoo_ticker).fast_info.last_price
    except Exception:
        return None
    try:
        value = float(price)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _cell(frame: pd.DataFrame, row: object, col: str) -> float | None:
    try:
        value = float(frame.at[row, col])  # type: ignore[arg-type]  # .at is typed as Any-ish scalar
    except (KeyError, TypeError, ValueError):
        return None
    return None if pd.isna(value) else value


def repair_last_session(df: pd.DataFrame, yahoo_ticker: str) -> tuple[pd.DataFrame, str]:
    """Fills the newest candle when Yahoo publishes it without a Close.

    For GPW symbols the freshest daily bar regularly arrives with Open/High/Low/Volume
    but `Close=NaN` (US symbols are fine). `dropna(subset=["Close"])` in normalize_ohlcv
    then dropped the entire session, so /technical ran a session behind while every other
    agent already had the fresh price from `info` — one company, one day, two prices,
    depending on which endpoint you asked. On 2026-08-02 this hit all 18 GPW tickers of
    the daily review at once.

    The Close is taken from `fast_info.last_price` and accepted only when it lands inside
    that session's Low..High, so a stale or foreign quote cannot invent a candle. For the
    newest bar the adjustment factor is still 1.0 (no dividend/split has been applied to
    it yet), which is why unadjusted Open/High/Low can be mixed into an adjusted frame.
    """
    if df.empty or "Close" not in df.columns:
        return df, "none"
    last = df.index[-1]
    if not pd.isna(df.at[last, "Close"]):
        return df, "history"

    quote = _last_quote(yahoo_ticker)
    if quote is None:
        return df, "dropped"

    raw = flatten_columns(_download_unadjusted(yahoo_ticker, _REPAIR_LOOKBACK_DAYS))
    if raw.empty or last not in raw.index:
        return df, "dropped"

    low, high = _cell(raw, last, "Low"), _cell(raw, last, "High")
    if low is None or high is None:
        return df, "dropped"
    if not (low * (1 - _QUOTE_TOLERANCE) <= quote <= high * (1 + _QUOTE_TOLERANCE)):
        return df, "dropped"

    df = df.copy()
    for col in ("Open", "High", "Low", "Volume"):
        if col in df.columns and col in raw.columns and pd.isna(df.at[last, col]):
            df.at[last, col] = raw.at[last, col]
    df.at[last, "Close"] = quote
    return df, "fast_info"


def fetch_ohlcv(ticker: str, days_back: int = 90) -> pd.DataFrame:
    yahoo_ticker = to_yahoo_ticker(ticker)
    raw = download_ohlcv(yahoo_ticker, ticker, days_back)
    repaired, close_source = repair_last_session(flatten_columns(raw), yahoo_ticker)
    df = normalize_ohlcv(repaired, ticker)
    validate_columns(df, ticker)
    df.attrs["last_close_source"] = close_source
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
        # "history" = closing price straight from the candle, "fast_info" = the candle
        # arrived without a Close and it was filled from the live quote (see repair_last_session).
        "last_close_source": df.attrs.get("last_close_source"),
    }
