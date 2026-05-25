import pandas as pd
import pandas_ta as ta

SMA_SHORT = 20
SMA_MID = 50
SMA_LONG = 200
EMA_SHORT = 20
EMA_MID = 50

RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
STOCH_K = 14
STOCH_D = 3
STOCH_SMOOTH = 3
STOCHRSI_LENGTH = 14
STOCHRSI_RSI = 14
STOCHRSI_K = 3
STOCHRSI_D = 3
CCI_LENGTH = 20
WILLR_LENGTH = 14
ROC_LENGTH = 10
TSI_FAST = 13
TSI_SLOW = 25
TSI_SIGNAL = 13

ADX_LENGTH = 14
SUPERTREND_LENGTH = 7
SUPERTREND_MULT = 3.0
AROON_LENGTH = 25
ICHIMOKU_TENKAN = 9
ICHIMOKU_KIJUN = 26
ICHIMOKU_SENKOU = 52

BB_PERIOD = 20
ATR_PERIOD = 14
KC_LENGTH = 20
KC_SCALAR = 2
DONCHIAN_LENGTH = 20
PSAR_AF = 0.02
PSAR_MAX_AF = 0.2

CMF_LENGTH = 20
MFI_LENGTH = 14


def add_sma(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["SMA_20"] = ta.sma(df["Close"], length=SMA_SHORT)
    df["SMA_50"] = ta.sma(df["Close"], length=SMA_MID)
    df["SMA_200"] = ta.sma(df["Close"], length=SMA_LONG)
    return df


def add_ema(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["EMA_20"] = ta.ema(df["Close"], length=EMA_SHORT)
    df["EMA_50"] = ta.ema(df["Close"], length=EMA_MID)
    return df


def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["RSI_14"] = ta.rsi(df["Close"], length=RSI_PERIOD)
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    macd = ta.macd(df["Close"], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
    df["MACD"] = macd[f"MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"]
    df["MACD_signal"] = macd[f"MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"]
    df["MACD_hist"] = macd[f"MACDh_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"]
    return df


def add_stoch(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    stoch = ta.stoch(df["High"], df["Low"], df["Close"],
                     k=STOCH_K, d=STOCH_D, smooth_k=STOCH_SMOOTH)
    df["STOCH_K"] = stoch[next(c for c in stoch.columns if c.startswith("STOCHk_"))]
    df["STOCH_D"] = stoch[next(c for c in stoch.columns if c.startswith("STOCHd_"))]
    return df


def add_stochrsi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    srsi = ta.stochrsi(df["Close"], length=STOCHRSI_LENGTH, rsi_length=STOCHRSI_RSI,
                       k=STOCHRSI_K, d=STOCHRSI_D)
    df["STOCHRSI_K"] = srsi[next(c for c in srsi.columns if c.startswith("STOCHRSIk_"))]
    df["STOCHRSI_D"] = srsi[next(c for c in srsi.columns if c.startswith("STOCHRSId_"))]
    return df


def add_cci(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    sma_tp = typical_price.rolling(CCI_LENGTH).mean()
    import numpy as np
    mad = typical_price.rolling(CCI_LENGTH).apply(
        lambda x: np.mean(np.abs(x - np.mean(x))), raw=True
    )
    df["CCI"] = (typical_price - sma_tp) / (0.015 * mad)
    return df


def add_willr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["WILLR"] = ta.willr(df["High"], df["Low"], df["Close"], length=WILLR_LENGTH)
    return df


def add_roc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ROC"] = ta.roc(df["Close"], length=ROC_LENGTH)
    return df


def add_tsi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    tsi = ta.tsi(df["Close"], fast=TSI_FAST, slow=TSI_SLOW, signal=TSI_SIGNAL)
    df["TSI"] = tsi[next(c for c in tsi.columns if c.startswith("TSI_"))]
    df["TSI_signal"] = tsi[next(c for c in tsi.columns if c.startswith("TSIs_"))]
    return df


def add_adx(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    adx = ta.adx(df["High"], df["Low"], df["Close"], length=ADX_LENGTH)
    df["ADX"] = adx[next(c for c in adx.columns if c.startswith("ADX_"))]
    df["ADX_pos"] = adx[next(c for c in adx.columns if c.startswith("DMP_"))]
    df["ADX_neg"] = adx[next(c for c in adx.columns if c.startswith("DMN_"))]
    return df


def add_supertrend(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    st = ta.supertrend(df["High"], df["Low"], df["Close"],
                       length=SUPERTREND_LENGTH, multiplier=SUPERTREND_MULT)
    df["SUPERT"] = st[next(c for c in st.columns if c.startswith("SUPERT_"))]
    df["SUPERT_dir"] = st[next(c for c in st.columns if c.startswith("SUPERTd_"))]
    return df


def add_aroon(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    aroon = ta.aroon(df["High"], df["Low"], length=AROON_LENGTH)
    df["AROON_up"] = aroon[next(c for c in aroon.columns if c.startswith("AROONU"))]
    df["AROON_down"] = aroon[next(c for c in aroon.columns if c.startswith("AROOND"))]
    df["AROON_osc"] = aroon[next(c for c in aroon.columns if c.startswith("AROONOSC"))]
    return df


def add_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    result = ta.ichimoku(df["High"], df["Low"], df["Close"],
                         tenkan=ICHIMOKU_TENKAN, kijun=ICHIMOKU_KIJUN, senkou=ICHIMOKU_SENKOU)
    ich = result[0] if isinstance(result, tuple) else result
    if ich is None:
        return df
    for col, prefix in [("ICH_tenkan", "ITS_"), ("ICH_kijun", "IKS_"),
                         ("ICH_span_a", "ISA_"), ("ICH_span_b", "ISB_")]:
        src = next((c for c in ich.columns if c.startswith(prefix)), None)
        if src:
            df[col] = ich[src]
    return df


def add_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bb = ta.bbands(df["Close"], length=BB_PERIOD)
    df["BB_upper"] = bb[next(c for c in bb.columns if c.startswith(f"BBU_{BB_PERIOD}"))]
    df["BB_mid"] = bb[next(c for c in bb.columns if c.startswith(f"BBM_{BB_PERIOD}"))]
    df["BB_lower"] = bb[next(c for c in bb.columns if c.startswith(f"BBL_{BB_PERIOD}"))]
    return df


def add_keltner_channel(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    kc = ta.kc(df["High"], df["Low"], df["Close"], length=KC_LENGTH, scalar=KC_SCALAR)
    df["KC_upper"] = kc[next(c for c in kc.columns if c.startswith("KCU"))]
    df["KC_mid"] = kc[next(c for c in kc.columns if c.startswith("KCB"))]
    df["KC_lower"] = kc[next(c for c in kc.columns if c.startswith("KCL"))]
    return df


def add_donchian(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    dc = ta.donchian(df["High"], df["Low"],
                     lower_length=DONCHIAN_LENGTH, upper_length=DONCHIAN_LENGTH)
    df["DC_upper"] = dc[next(c for c in dc.columns if c.startswith("DCU"))]
    df["DC_mid"] = dc[next(c for c in dc.columns if c.startswith("DCM"))]
    df["DC_lower"] = dc[next(c for c in dc.columns if c.startswith("DCL"))]
    return df


def add_atr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ATR_14"] = ta.atr(df["High"], df["Low"], df["Close"], length=ATR_PERIOD)
    return df


def add_psar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    psar = ta.psar(df["High"], df["Low"], df["Close"], af=PSAR_AF, max_af=PSAR_MAX_AF)
    df["PSAR_bull"] = psar[next(c for c in psar.columns if c.startswith("PSARl"))]
    df["PSAR_bear"] = psar[next(c for c in psar.columns if c.startswith("PSARs"))]
    return df


def add_obv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["OBV"] = ta.obv(df["Close"], df["Volume"])
    return df


def add_cmf(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["CMF"] = ta.cmf(df["High"], df["Low"], df["Close"], df["Volume"], length=CMF_LENGTH)
    return df


def add_mfi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["MFI"] = ta.mfi(df["High"], df["Low"], df["Close"], df["Volume"], length=MFI_LENGTH)
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_sma(df)
    df = add_ema(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_stoch(df)
    df = add_stochrsi(df)
    df = add_cci(df)
    df = add_willr(df)
    df = add_roc(df)
    df = add_tsi(df)
    df = add_adx(df)
    df = add_supertrend(df)
    df = add_aroon(df)
    df = add_ichimoku(df)
    df = add_bollinger_bands(df)
    df = add_keltner_channel(df)
    df = add_donchian(df)
    df = add_atr(df)
    df = add_psar(df)
    df = add_obv(df)
    df = add_cmf(df)
    df = add_mfi(df)
    return df
