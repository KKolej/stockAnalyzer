
from typing import Any

import pandas as pd

from .support_resistance import NEAR_ATR_MULT, analyze_support_resistance

RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
STOCH_OVERSOLD = 20
STOCH_OVERBOUGHT = 80
STOCHRSI_OVERSOLD = 20
STOCHRSI_OVERBOUGHT = 80
CCI_OVERSOLD = -100
CCI_OVERBOUGHT = 100
CCI_EXTREME = 200
WILLR_OVERSOLD = -80
WILLR_OVERBOUGHT = -20
ROC_STRONG = 5.0
ROC_MEDIUM = 2.0
CMF_STRONG = 0.2
CMF_MEDIUM = 0.05
MFI_OVERSOLD = 20
MFI_OVERBOUGHT = 80
ADX_STRONG = 40
ADX_MEDIUM = 25
TSI_STRONG = 25
AROON_STRONG = 70
VOLUME_SPIKE_MULT = 2.0
VOLUME_LOOKBACK = 20

Signal = dict[str, str]


def rsi_signal(row: pd.Series) -> Signal | None:
    rsi = row.get("RSI_14")
    if pd.isna(rsi):
        return None
    if rsi < RSI_OVERSOLD:
        return {"indicator": "RSI", "signal": "BULLISH", "strength": "strong",
                "note": f"RSI={rsi:.1f} — strefa wyprzedania"}
    if rsi > RSI_OVERBOUGHT:
        return {"indicator": "RSI", "signal": "BEARISH", "strength": "strong",
                "note": f"RSI={rsi:.1f} — strefa wykupienia"}
    return None


def macd_signal(row: pd.Series) -> Signal | None:
    macd = row.get("MACD")
    signal_line = row.get("MACD_signal")
    hist = row.get("MACD_hist")
    if pd.isna(macd) or pd.isna(signal_line):
        return None
    # Do not emit a signal when the histogram is near zero (no resolution)
    if hist is not None and not pd.isna(hist) and abs(hist) < 0.001:
        return None
    diff = macd - signal_line
    ref = max(abs(macd), abs(signal_line), 1e-9)
    if abs(diff) / ref < 0.02:
        return None
    if diff > 0:
        return {"indicator": "MACD", "signal": "BULLISH", "strength": "medium",
                "note": f"MACD={macd:.3f} powyżej sygnału {signal_line:.3f}"}
    return {"indicator": "MACD", "signal": "BEARISH", "strength": "medium",
            "note": f"MACD={macd:.3f} poniżej sygnału {signal_line:.3f}"}


def stoch_signal(row: pd.Series) -> Signal | None:
    k = row.get("STOCH_K")
    if pd.isna(k):
        return None
    if k < STOCH_OVERSOLD:
        return {"indicator": "Stochastic", "signal": "BULLISH", "strength": "strong",
                "note": f"%K={k:.1f} — strefa wyprzedania (<{STOCH_OVERSOLD})"}
    if k > STOCH_OVERBOUGHT:
        return {"indicator": "Stochastic", "signal": "BEARISH", "strength": "strong",
                "note": f"%K={k:.1f} — strefa wykupienia (>{STOCH_OVERBOUGHT})"}
    return None


def stochrsi_signal(row: pd.Series) -> Signal | None:
    k = row.get("STOCHRSI_K")
    if pd.isna(k):
        return None
    if k < STOCHRSI_OVERSOLD:
        return {"indicator": "StochRSI", "signal": "BULLISH", "strength": "medium",
                "note": f"StochRSI %K={k:.1f} — strefa wyprzedania"}
    if k > STOCHRSI_OVERBOUGHT:
        return {"indicator": "StochRSI", "signal": "BEARISH", "strength": "medium",
                "note": f"StochRSI %K={k:.1f} — strefa wykupienia"}
    return None


def cci_signal(row: pd.Series) -> Signal | None:
    cci = row.get("CCI")
    if pd.isna(cci):
        return None
    if cci < -CCI_EXTREME:
        return {"indicator": "CCI", "signal": "BULLISH", "strength": "strong",
                "note": f"CCI={cci:.1f} — ekstremalne wyprzedanie (<-{CCI_EXTREME})"}
    if cci < CCI_OVERSOLD:
        return {"indicator": "CCI", "signal": "BULLISH", "strength": "medium",
                "note": f"CCI={cci:.1f} — strefa wyprzedania (<{CCI_OVERSOLD})"}
    if cci > CCI_EXTREME:
        return {"indicator": "CCI", "signal": "BEARISH", "strength": "strong",
                "note": f"CCI={cci:.1f} — ekstremalne wykupienie (>{CCI_EXTREME})"}
    if cci > CCI_OVERBOUGHT:
        return {"indicator": "CCI", "signal": "BEARISH", "strength": "medium",
                "note": f"CCI={cci:.1f} — strefa wykupienia (>{CCI_OVERBOUGHT})"}
    return None


def willr_signal(row: pd.Series) -> Signal | None:
    willr = row.get("WILLR")
    if pd.isna(willr):
        return None
    if willr < WILLR_OVERSOLD:
        return {"indicator": "Williams %R", "signal": "BULLISH", "strength": "medium",
                "note": f"W%R={willr:.1f} — strefa wyprzedania (<{WILLR_OVERSOLD})"}
    if willr > WILLR_OVERBOUGHT:
        return {"indicator": "Williams %R", "signal": "BEARISH", "strength": "medium",
                "note": f"W%R={willr:.1f} — strefa wykupienia (>{WILLR_OVERBOUGHT})"}
    return None


def roc_signal(row: pd.Series) -> Signal | None:
    roc = row.get("ROC")
    if pd.isna(roc):
        return None
    if roc > ROC_STRONG:
        return {"indicator": "ROC", "signal": "BULLISH", "strength": "strong",
                "note": f"ROC={roc:.2f}% — silne dodatnie momentum"}
    if roc > ROC_MEDIUM:
        return {"indicator": "ROC", "signal": "BULLISH", "strength": "medium",
                "note": f"ROC={roc:.2f}% — dodatnie momentum"}
    if roc < -ROC_STRONG:
        return {"indicator": "ROC", "signal": "BEARISH", "strength": "strong",
                "note": f"ROC={roc:.2f}% — silne ujemne momentum"}
    if roc < -ROC_MEDIUM:
        return {"indicator": "ROC", "signal": "BEARISH", "strength": "medium",
                "note": f"ROC={roc:.2f}% — ujemne momentum"}
    return None


def tsi_signal(row: pd.Series) -> Signal | None:
    tsi = row.get("TSI")
    tsi_sig = row.get("TSI_signal")
    if pd.isna(tsi) or pd.isna(tsi_sig):
        return None
    if tsi > tsi_sig and tsi > 0:
        return {"indicator": "TSI", "signal": "BULLISH",
                "strength": "strong" if tsi > TSI_STRONG else "medium",
                "note": f"TSI={tsi:.1f} powyżej sygnału {tsi_sig:.1f}"}
    if tsi < tsi_sig and tsi < 0:
        return {"indicator": "TSI", "signal": "BEARISH",
                "strength": "strong" if tsi < -TSI_STRONG else "medium",
                "note": f"TSI={tsi:.1f} poniżej sygnału {tsi_sig:.1f}"}
    return None


def sma_cross_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    sma50 = row.get("SMA_50")
    sma200 = row.get("SMA_200")
    if pd.isna(close) or pd.isna(sma50) or pd.isna(sma200):
        return None
    if sma50 > sma200 and close > sma50:
        return {"indicator": "SMA Cross", "signal": "BULLISH", "strength": "strong",
                "note": f"Golden cross — SMA50={sma50:.2f} > SMA200={sma200:.2f}"}
    if sma50 < sma200 and close < sma50:
        return {"indicator": "SMA Cross", "signal": "BEARISH", "strength": "strong",
                "note": f"Death cross — SMA50={sma50:.2f} < SMA200={sma200:.2f}"}
    return None


def adx_signal(row: pd.Series) -> Signal | None:
    adx = row.get("ADX")
    adx_pos = row.get("ADX_pos")
    adx_neg = row.get("ADX_neg")
    if pd.isna(adx) or pd.isna(adx_pos) or pd.isna(adx_neg) or adx < ADX_MEDIUM:
        return None
    strength = "strong" if adx > ADX_STRONG else "medium"
    if adx_pos > adx_neg:
        return {"indicator": "ADX", "signal": "BULLISH", "strength": strength,
                "note": f"ADX={adx:.1f}, +DI={adx_pos:.1f} > -DI={adx_neg:.1f} — trend wzrostowy"}
    return {"indicator": "ADX", "signal": "BEARISH", "strength": strength,
            "note": f"ADX={adx:.1f}, -DI={adx_neg:.1f} > +DI={adx_pos:.1f} — trend spadkowy"}


def supertrend_signal(row: pd.Series) -> Signal | None:
    direction = row.get("SUPERT_dir")
    supert = row.get("SUPERT")
    close = row.get("Close")
    if direction is None or pd.isna(direction) or pd.isna(supert):
        return None
    if direction == 1:
        return {"indicator": "Supertrend", "signal": "BULLISH", "strength": "medium",
                "note": f"Cena {close:.2f} powyżej Supertrend {supert:.2f}"}
    return {"indicator": "Supertrend", "signal": "BEARISH", "strength": "medium",
            "note": f"Cena {close:.2f} poniżej Supertrend {supert:.2f}"}


def aroon_signal(row: pd.Series) -> Signal | None:
    up = row.get("AROON_up")
    down = row.get("AROON_down")
    if pd.isna(up) or pd.isna(down):
        return None
    if up > AROON_STRONG and up > down:
        return {"indicator": "Aroon", "signal": "BULLISH",
                "strength": "strong" if up > 90 else "medium",
                "note": f"Aroon Up={up:.0f} dominuje nad Down={down:.0f}"}
    if down > AROON_STRONG and down > up:
        return {"indicator": "Aroon", "signal": "BEARISH",
                "strength": "strong" if down > 90 else "medium",
                "note": f"Aroon Down={down:.0f} dominuje nad Up={up:.0f}"}
    return None


def ichimoku_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    tenkan = row.get("ICH_tenkan")
    kijun = row.get("ICH_kijun")
    if pd.isna(close) or pd.isna(tenkan) or pd.isna(kijun):
        return None
    if close > tenkan and close > kijun and tenkan > kijun:
        return {"indicator": "Ichimoku", "signal": "BULLISH", "strength": "strong",
                "note": f"Cena powyżej Tenkan ({tenkan:.2f}) i Kijun ({kijun:.2f})"}
    if close < tenkan and close < kijun and tenkan < kijun:
        return {"indicator": "Ichimoku", "signal": "BEARISH", "strength": "strong",
                "note": f"Cena poniżej Tenkan ({tenkan:.2f}) i Kijun ({kijun:.2f})"}
    return None


def bollinger_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    bb_upper = row.get("BB_upper")
    bb_lower = row.get("BB_lower")
    if pd.isna(close) or pd.isna(bb_upper) or pd.isna(bb_lower):
        return None
    if close < bb_lower:
        return {"indicator": "Bollinger Bands", "signal": "BULLISH", "strength": "medium",
                "note": f"Cena {close:.2f} poniżej dolnego BB {bb_lower:.2f}"}
    if close > bb_upper:
        return {"indicator": "Bollinger Bands", "signal": "BEARISH", "strength": "medium",
                "note": f"Cena {close:.2f} powyżej górnego BB {bb_upper:.2f}"}
    return None


def keltner_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    kc_upper = row.get("KC_upper")
    kc_lower = row.get("KC_lower")
    if pd.isna(close) or pd.isna(kc_upper) or pd.isna(kc_lower):
        return None
    if close < kc_lower:
        return {"indicator": "Keltner Channel", "signal": "BULLISH", "strength": "medium",
                "note": f"Cena {close:.2f} poniżej dolnego KC {kc_lower:.2f}"}
    if close > kc_upper:
        return {"indicator": "Keltner Channel", "signal": "BEARISH", "strength": "medium",
                "note": f"Cena {close:.2f} powyżej górnego KC {kc_upper:.2f}"}
    return None


def donchian_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    dc_upper = row.get("DC_upper")
    dc_lower = row.get("DC_lower")
    if pd.isna(close) or pd.isna(dc_upper) or pd.isna(dc_lower):
        return None
    if close >= dc_upper:
        return {"indicator": "Donchian", "signal": "BULLISH", "strength": "medium",
                "note": f"Cena {close:.2f} przy górnym kanale {dc_upper:.2f} — wybicie"}
    if close <= dc_lower:
        return {"indicator": "Donchian", "signal": "BEARISH", "strength": "medium",
                "note": f"Cena {close:.2f} przy dolnym kanale {dc_lower:.2f} — przełamanie"}
    return None


def psar_signal(row: pd.Series) -> Signal | None:
    close = row.get("Close")
    psar_bull = row.get("PSAR_bull")
    psar_bear = row.get("PSAR_bear")
    if pd.isna(close):
        return None
    if psar_bull is not None and not pd.isna(psar_bull):
        return {"indicator": "PSAR", "signal": "BULLISH", "strength": "medium",
                "note": f"Cena {close:.2f} powyżej PSAR {psar_bull:.2f} — trend wzrostowy"}
    if psar_bear is not None and not pd.isna(psar_bear):
        return {"indicator": "PSAR", "signal": "BEARISH", "strength": "medium",
                "note": f"Cena {close:.2f} poniżej PSAR {psar_bear:.2f} — trend spadkowy"}
    return None


def cmf_signal(row: pd.Series) -> Signal | None:
    cmf = row.get("CMF")
    if pd.isna(cmf):
        return None
    if cmf > CMF_STRONG:
        return {"indicator": "CMF", "signal": "BULLISH", "strength": "strong",
                "note": f"CMF={cmf:.3f} — silny napływ kapitału"}
    if cmf > CMF_MEDIUM:
        return {"indicator": "CMF", "signal": "BULLISH", "strength": "medium",
                "note": f"CMF={cmf:.3f} — napływ kapitału"}
    if cmf < -CMF_STRONG:
        return {"indicator": "CMF", "signal": "BEARISH", "strength": "strong",
                "note": f"CMF={cmf:.3f} — silny odpływ kapitału"}
    if cmf < -CMF_MEDIUM:
        return {"indicator": "CMF", "signal": "BEARISH", "strength": "medium",
                "note": f"CMF={cmf:.3f} — odpływ kapitału"}
    return None


def mfi_signal(row: pd.Series) -> Signal | None:
    mfi = row.get("MFI")
    if pd.isna(mfi):
        return None
    if mfi < MFI_OVERSOLD:
        return {"indicator": "MFI", "signal": "BULLISH", "strength": "strong",
                "note": f"MFI={mfi:.1f} — wyprzedanie wolumenowe"}
    if mfi > MFI_OVERBOUGHT:
        return {"indicator": "MFI", "signal": "BEARISH", "strength": "strong",
                "note": f"MFI={mfi:.1f} — wykupienie wolumenowe"}
    return None


def volume_spike_signal(df: pd.DataFrame) -> Signal | None:
    if len(df) < VOLUME_LOOKBACK + 1:
        return None
    last_volume = df["Volume"].iloc[-1]
    avg_volume = df["Volume"].iloc[-VOLUME_LOOKBACK - 1: -1].mean()
    if pd.isna(last_volume) or pd.isna(avg_volume) or avg_volume == 0:
        return None
    ratio = last_volume / avg_volume
    if ratio >= VOLUME_SPIKE_MULT:
        return {
            "indicator": "Wolumen",
            "signal": "NEUTRAL",
            "strength": "strong",
            "note": (
                f"Wolumen {last_volume:,.0f} — "
                f"{ratio:.1f}x powyżej śr. 20-sesyjnej (wzmocnienie sygnału)"
            ),
        }
    return None


def _strength_from_touches(touches: int) -> str:
    if touches >= 3:
        return "strong"
    if touches == 2:
        return "medium"
    return "weak"


def support_resistance_signal(sr: dict[str, Any]) -> Signal | None:
    """Signal when price sits right at a support zone (bullish) or resistance (bearish)."""
    price = sr.get("price")
    atr = sr.get("atr")
    sup = sr.get("nearest_support")
    res = sr.get("nearest_resistance")
    if not price:
        return None

    # proximity threshold: 0.5×ATR, or 1% of price when ATR is missing
    threshold = (atr * NEAR_ATR_MULT) if atr else (price * 0.01)

    dist_sup = abs(price - sup["price"]) if sup is not None else None
    dist_res = abs(res["price"] - price) if res is not None else None

    # support wins when it is closer (or the only level in range)
    if sup is not None and dist_sup is not None and dist_sup <= threshold and (
        dist_res is None or dist_sup <= dist_res
    ):
        return {"indicator": "Wsparcie", "signal": "BULLISH",
                "strength": _strength_from_touches(sup["touches"]),
                "note": f"Cena {price:.2f} przy wsparciu {sup['price']:.2f} "
                        f"({sup['touches']} dotknięć) — szansa na odbicie"}
    if res is not None and dist_res is not None and dist_res <= threshold:
        return {"indicator": "Opór", "signal": "BEARISH",
                "strength": _strength_from_touches(res["touches"]),
                "note": f"Cena {price:.2f} przy oporze {res['price']:.2f} "
                        f"({res['touches']} dotknięć) — ryzyko odrzucenia"}
    return None


def generate_signals(df: pd.DataFrame) -> list[Signal]:
    row = df.iloc[-1]
    sr = analyze_support_resistance(df)
    candidates = [
        rsi_signal(row),
        stoch_signal(row),
        stochrsi_signal(row),
        macd_signal(row),
        tsi_signal(row),
        cci_signal(row),
        willr_signal(row),
        roc_signal(row),
        sma_cross_signal(row),
        adx_signal(row),
        supertrend_signal(row),
        aroon_signal(row),
        ichimoku_signal(row),
        bollinger_signal(row),
        keltner_signal(row),
        donchian_signal(row),
        psar_signal(row),
        cmf_signal(row),
        mfi_signal(row),
        volume_spike_signal(df),
        support_resistance_signal(sr),
    ]
    return [s for s in candidates if s is not None]
