import pandas as pd
import pandas_ta as ta

SMA_SHORT = 20
SMA_MID = 50
SMA_LONG = 200
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
ATR_PERIOD = 14


def add_sma(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[f"SMA_{SMA_SHORT}"] = ta.sma(df["Close"], length=SMA_SHORT)
    df[f"SMA_{SMA_MID}"] = ta.sma(df["Close"], length=SMA_MID)
    df[f"SMA_{SMA_LONG}"] = ta.sma(df["Close"], length=SMA_LONG)
    return df


def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[f"RSI_{RSI_PERIOD}"] = ta.rsi(df["Close"], length=RSI_PERIOD)
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    macd = ta.macd(df["Close"], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
    df["MACD"] = macd[f"MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"]
    df["MACD_signal"] = macd[f"MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"]
    df["MACD_hist"] = macd[f"MACDh_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"]
    return df


def add_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bb = ta.bbands(df["Close"], length=BB_PERIOD)
    upper_col = next(c for c in bb.columns if c.startswith(f"BBU_{BB_PERIOD}"))
    mid_col = next(c for c in bb.columns if c.startswith(f"BBM_{BB_PERIOD}"))
    lower_col = next(c for c in bb.columns if c.startswith(f"BBL_{BB_PERIOD}"))
    df["BB_upper"] = bb[upper_col]
    df["BB_mid"] = bb[mid_col]
    df["BB_lower"] = bb[lower_col]
    return df


def add_atr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[f"ATR_{ATR_PERIOD}"] = ta.atr(df["High"], df["Low"], df["Close"], length=ATR_PERIOD)
    return df


def add_obv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["OBV"] = ta.obv(df["Close"], df["Volume"])
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_sma(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_atr(df)
    df = add_obv(df)
    return df
