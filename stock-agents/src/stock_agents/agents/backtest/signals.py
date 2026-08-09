"""Point-in-time signal events for the reliability backtest.

Every rule may look ONLY at data available on the day it fires — that is the whole
reason a measured hit rate means anything. Rolling indicators satisfy this by
construction; look-ahead normally sneaks in through normalisation fitted on the entire
series, so nothing here is scaled or fitted globally.

Rules describe EVENTS (a crossing), not states. A state like "RSI below 30" would count
the same episode ten times and inflate the sample with ten copies of one observation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

BULLISH = "bullish"
BEARISH = "bearish"


@dataclass(frozen=True)
class SignalRule:
    key: str
    note: str
    direction: str
    detect: Callable[[pd.DataFrame], pd.Series]


def _empty(df: pd.DataFrame) -> pd.Series:
    return pd.Series(False, index=df.index)


def _col(df: pd.DataFrame, name: str) -> pd.Series | None:
    if name not in df.columns:
        return None
    s = pd.to_numeric(df[name], errors="coerce")
    return s if s.notna().any() else None


def _cross_above(series: pd.Series, level: pd.Series | float) -> pd.Series:
    prev = series.shift(1)
    lvl_prev = level.shift(1) if isinstance(level, pd.Series) else level
    return (series > level) & (prev <= lvl_prev)


def _cross_below(series: pd.Series, level: pd.Series | float) -> pd.Series:
    prev = series.shift(1)
    lvl_prev = level.shift(1) if isinstance(level, pd.Series) else level
    return (series < level) & (prev >= lvl_prev)


def _rsi_oversold(df: pd.DataFrame) -> pd.Series:
    rsi = _col(df, "RSI_14")
    return _empty(df) if rsi is None else _cross_below(rsi, 30.0)


def _rsi_overbought(df: pd.DataFrame) -> pd.Series:
    rsi = _col(df, "RSI_14")
    return _empty(df) if rsi is None else _cross_above(rsi, 70.0)


def _macd_cross_up(df: pd.DataFrame) -> pd.Series:
    macd, sig = _col(df, "MACD"), _col(df, "MACD_signal")
    return _empty(df) if macd is None or sig is None else _cross_above(macd, sig)


def _macd_cross_down(df: pd.DataFrame) -> pd.Series:
    macd, sig = _col(df, "MACD"), _col(df, "MACD_signal")
    return _empty(df) if macd is None or sig is None else _cross_below(macd, sig)


def _sma_cross_up(df: pd.DataFrame) -> pd.Series:
    fast, slow = _col(df, "SMA_20"), _col(df, "SMA_50")
    return _empty(df) if fast is None or slow is None else _cross_above(fast, slow)


def _sma_cross_down(df: pd.DataFrame) -> pd.Series:
    fast, slow = _col(df, "SMA_20"), _col(df, "SMA_50")
    return _empty(df) if fast is None or slow is None else _cross_below(fast, slow)


def _below_bb_lower(df: pd.DataFrame) -> pd.Series:
    close, band = _col(df, "Close"), _col(df, "BB_lower")
    return _empty(df) if close is None or band is None else _cross_below(close, band)


def _above_bb_upper(df: pd.DataFrame) -> pd.Series:
    close, band = _col(df, "Close"), _col(df, "BB_upper")
    return _empty(df) if close is None or band is None else _cross_above(close, band)


def _volume_spike_up(df: pd.DataFrame) -> pd.Series:
    close, vol = _col(df, "Close"), _col(df, "Volume")
    if close is None or vol is None:
        return _empty(df)
    # `shift(1)` on the average: the day's own volume must not sit in the baseline
    # it is being compared against.
    avg = vol.rolling(20).mean().shift(1)
    return (vol > 2.0 * avg) & (close > close.shift(1))


def _new_52w_high(df: pd.DataFrame) -> pd.Series:
    close = _col(df, "Close")
    if close is None:
        return _empty(df)
    prev_max = close.rolling(252).max().shift(1)
    return close > prev_max


def _new_52w_low(df: pd.DataFrame) -> pd.Series:
    close = _col(df, "Close")
    if close is None:
        return _empty(df)
    prev_min = close.rolling(252).min().shift(1)
    return close < prev_min


def _adx_trend_up(df: pd.DataFrame) -> pd.Series:
    adx, pos, neg = _col(df, "ADX"), _col(df, "ADX_pos"), _col(df, "ADX_neg")
    if adx is None or pos is None or neg is None:
        return _empty(df)
    return _cross_above(adx, 25.0) & (pos > neg)


# Notes are Polish because they end up in the report; keys stay stable and English.
RULES: tuple[SignalRule, ...] = (
    SignalRule("rsi_oversold_30", "RSI spadł poniżej 30 (wyprzedanie)", BULLISH, _rsi_oversold),
    SignalRule("rsi_overbought_70", "RSI przebił 70 (wykupienie)", BEARISH, _rsi_overbought),
    SignalRule("macd_cross_up", "MACD przeciął linię sygnału od dołu", BULLISH, _macd_cross_up),
    SignalRule("macd_cross_down", "MACD przeciął linię sygnału od góry", BEARISH, _macd_cross_down),
    SignalRule("sma20_over_sma50", "SMA20 przecięła SMA50 od dołu", BULLISH, _sma_cross_up),
    SignalRule("sma20_under_sma50", "SMA20 przecięła SMA50 od góry", BEARISH, _sma_cross_down),
    SignalRule("close_below_bb", "Kurs zszedł pod dolną wstęgę Bollingera", BULLISH, _below_bb_lower),
    SignalRule("close_above_bb", "Kurs wyszedł nad górną wstęgę Bollingera", BEARISH, _above_bb_upper),
    SignalRule("volume_spike_up", "Wolumen 2× powyżej średniej przy wzroście kursu", BULLISH, _volume_spike_up),
    SignalRule("new_52w_high", "Nowe maksimum 52-tygodniowe", BULLISH, _new_52w_high),
    SignalRule("new_52w_low", "Nowe minimum 52-tygodniowe", BEARISH, _new_52w_low),
    SignalRule("adx_trend_start", "ADX przebił 25 przy przewadze strony popytowej", BULLISH, _adx_trend_up),
)
