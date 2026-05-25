import pandas as pd
import yfinance as yf

GPW_SUFFIX = ".WA"
US_INPUT_SUFFIX = ".US"

GPW_TICKER_OVERRIDES: dict[str, str] = {
    "KGHM": "KGH",
}

REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}


class FetchError(Exception):
    pass


def to_yahoo_ticker(ticker: str) -> str:
    upper = ticker.upper()
    if upper.endswith(US_INPUT_SUFFIX):
        return upper.removesuffix(US_INPUT_SUFFIX)
    base = GPW_TICKER_OVERRIDES.get(upper, upper)
    return base + GPW_SUFFIX


def download_ohlcv(yahoo_ticker: str, ticker: str, days_back: int) -> pd.DataFrame:
    period = f"{days_back}d"
    df = yf.download(
        yahoo_ticker,
        period=period,
        interval="1d",
        auto_adjust=False,
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
    df = df.rename(columns={"Adj Close": "Adj_Close"})
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
