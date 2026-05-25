
import pandas as pd

RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
VOLUME_SPIKE_MULTIPLIER = 2.0
VOLUME_LOOKBACK = 20

Signal = dict[str, str]


def rsi_signal(row: pd.Series) -> Signal | None:
    rsi = row.get("RSI_14")
    if pd.isna(rsi):
        return None
    if rsi < RSI_OVERSOLD:
        return {
            "indicator": "RSI",
            "signal": "BULLISH",
            "strength": "strong",
            "note": f"RSI={rsi:.1f} — strefa wyprzedania, możliwe odbicie",
        }
    if rsi > RSI_OVERBOUGHT:
        return {
            "indicator": "RSI",
            "signal": "BEARISH",
            "strength": "strong",
            "note": f"RSI={rsi:.1f} — strefa wykupienia, możliwa korekta",
        }
    return None


def macd_signal(row: pd.Series) -> Signal | None:
    macd = row.get("MACD")
    signal_line = row.get("MACD_signal")
    if pd.isna(macd) or pd.isna(signal_line):
        return None
    if macd > signal_line:
        return {
            "indicator": "MACD",
            "signal": "BULLISH",
            "strength": "medium",
            "note": f"MACD={macd:.3f} powyżej linii sygnału {signal_line:.3f}",
        }
    return {
        "indicator": "MACD",
        "signal": "BEARISH",
        "strength": "medium",
        "note": f"MACD={macd:.3f} poniżej linii sygnału {signal_line:.3f}",
    }


def bollinger_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    bb_upper = row.get("BB_upper")
    bb_lower = row.get("BB_lower")
    if pd.isna(close) or pd.isna(bb_upper) or pd.isna(bb_lower):
        return None
    if close < bb_lower:
        return {
            "indicator": "Bollinger Bands",
            "signal": "BULLISH",
            "strength": "medium",
            "note": f"Cena {close:.2f} poniżej dolnego BB {bb_lower:.2f}",
        }
    if close > bb_upper:
        return {
            "indicator": "Bollinger Bands",
            "signal": "BEARISH",
            "strength": "medium",
            "note": f"Cena {close:.2f} powyżej górnego BB {bb_upper:.2f}",
        }
    return None


def sma_cross_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    sma50 = row.get("SMA_50")
    sma200 = row.get("SMA_200")
    if pd.isna(close) or pd.isna(sma50) or pd.isna(sma200):
        return None
    if sma50 > sma200 and close > sma50:
        return {
            "indicator": "SMA Cross",
            "signal": "BULLISH",
            "strength": "strong",
            "note": f"Golden cross — SMA50={sma50:.2f} > SMA200={sma200:.2f}, cena powyżej SMA50",
        }
    if sma50 < sma200 and close < sma50:
        return {
            "indicator": "SMA Cross",
            "signal": "BEARISH",
            "strength": "strong",
            "note": f"Death cross — SMA50={sma50:.2f} < SMA200={sma200:.2f}, cena poniżej SMA50",
        }
    return None


def volume_confirmation_signal(df: pd.DataFrame) -> Signal | None:
    if len(df) < VOLUME_LOOKBACK + 1:
        return None
    last_volume = df["Volume"].iloc[-1]
    avg_volume = df["Volume"].iloc[-VOLUME_LOOKBACK - 1 : -1].mean()
    if pd.isna(last_volume) or pd.isna(avg_volume) or avg_volume == 0:
        return None
    if last_volume >= avg_volume * VOLUME_SPIKE_MULTIPLIER:
        return {
            "indicator": "Wolumen",
            "signal": "NEUTRAL",
            "strength": "strong",
            "note": (
                f"Wolumen {last_volume:,.0f} — "
                f"{last_volume / avg_volume:.1f}x powyżej śr. 20-sesyjnej (wzmocnienie sygnału)"
            ),
        }
    return None


def generate_signals(df: pd.DataFrame) -> list[Signal]:
    last_row = df.iloc[-1]
    raw_signals = [
        rsi_signal(last_row),
        macd_signal(last_row),
        bollinger_signal(last_row),
        sma_cross_signal(last_row),
        volume_confirmation_signal(df),
    ]
    return [s for s in raw_signals if s is not None]
