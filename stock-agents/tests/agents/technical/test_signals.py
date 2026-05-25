import pandas as pd

from stock_agents.agents.technical.signals import (
    bollinger_signal,
    macd_signal,
    rsi_signal,
    sma_cross_signal,
)


def make_row(**kwargs: float) -> pd.Series:
    return pd.Series(kwargs)


def test_rsi_oversold_is_bullish() -> None:
    signal = rsi_signal(make_row(RSI_14=25.0))
    assert signal is not None
    assert signal["signal"] == "BULLISH"
    assert signal["strength"] == "strong"


def test_rsi_overbought_is_bearish() -> None:
    signal = rsi_signal(make_row(RSI_14=75.0))
    assert signal is not None
    assert signal["signal"] == "BEARISH"


def test_rsi_neutral_returns_none() -> None:
    assert rsi_signal(make_row(RSI_14=50.0)) is None


def test_rsi_missing_returns_none() -> None:
    assert rsi_signal(make_row(RSI_14=float("nan"))) is None


def test_macd_above_signal_is_bullish() -> None:
    signal = macd_signal(make_row(MACD=0.5, MACD_signal=0.1))
    assert signal is not None
    assert signal["signal"] == "BULLISH"


def test_macd_below_signal_is_bearish() -> None:
    signal = macd_signal(make_row(MACD=-0.2, MACD_signal=0.1))
    assert signal is not None
    assert signal["signal"] == "BEARISH"


def test_bollinger_below_lower_is_bullish() -> None:
    signal = bollinger_signal(make_row(Close=9.0, BB_upper=12.0, BB_lower=10.0))
    assert signal is not None
    assert signal["signal"] == "BULLISH"


def test_bollinger_above_upper_is_bearish() -> None:
    signal = bollinger_signal(make_row(Close=13.0, BB_upper=12.0, BB_lower=10.0))
    assert signal is not None
    assert signal["signal"] == "BEARISH"


def test_golden_cross_is_bullish_strong() -> None:
    signal = sma_cross_signal(make_row(Close=55.0, SMA_50=52.0, SMA_200=48.0))
    assert signal is not None
    assert signal["signal"] == "BULLISH"
    assert signal["strength"] == "strong"


def test_death_cross_is_bearish_strong() -> None:
    signal = sma_cross_signal(make_row(Close=45.0, SMA_50=48.0, SMA_200=52.0))
    assert signal is not None
    assert signal["signal"] == "BEARISH"
    assert signal["strength"] == "strong"
