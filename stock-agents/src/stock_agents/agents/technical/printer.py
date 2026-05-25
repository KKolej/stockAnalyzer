import pandas as pd

SIGNAL_ICON = {"BULLISH": "▲", "BEARISH": "▼", "NEUTRAL": "─"}
STRENGTH_ORDER = {"strong": 3, "medium": 2, "weak": 1}
SEPARATOR = "─" * 64
COL_NAME = 26


def v(value: object, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/d"
    return f"{value:.{decimals}f}"


def pair(a: object, b: object, decimals: int = 2) -> str:
    return f"{v(a, decimals)} / {v(b, decimals)}"


def triple(a: object, b: object, c: object, decimals: int = 2) -> str:
    return f"{v(a, decimals)} / {v(b, decimals)} / {v(c, decimals)}"


def row(name: str, value: str) -> str:
    return f"  {name:<{COL_NAME}} {value}"


def section_header(title: str) -> str:
    return f"\n  ▸ {title}\n  {'─' * 44}"


def format_change(current: float, previous: float) -> str:
    if previous == 0:
        return "n/d"
    pct = (current - previous) / previous * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def print_header(ticker: str, df: pd.DataFrame) -> None:
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last
    date_str = pd.to_datetime(last["Date"]).strftime("%Y-%m-%d")
    change_str = format_change(last["Close"], prev["Close"])
    print(SEPARATOR)
    print(f"  {ticker.upper():<12} {last['Close']:>10.2f}   {change_str:>8}   {date_str}")
    print(SEPARATOR)


def print_indicators(df: pd.DataFrame) -> None:
    g = df.iloc[-1].get

    print(section_header("TREND"))
    print(row("SMA 20 / 50 / 200", triple(g("SMA_20"), g("SMA_50"), g("SMA_200"))))
    print(row("EMA 20 / 50", pair(g("EMA_20"), g("EMA_50"))))
    print(row("ADX", v(g("ADX"))))
    print(row("ADX+ / ADX-", pair(g("ADX_pos"), g("ADX_neg"))))

    supert_dir = g("SUPERT_dir")
    supert_val = g("SUPERT")
    if supert_dir is not None and not pd.isna(supert_dir):
        icon = "▲" if supert_dir == 1 else "▼"
        print(row("Supertrend", f"{icon} {v(supert_val)}"))
    else:
        print(row("Supertrend", "n/d"))

    print(row("Aroon Up / Down", pair(g("AROON_up"), g("AROON_down"), 0)))
    print(row("Ich. Tenkan / Kijun", pair(g("ICH_tenkan"), g("ICH_kijun"))))
    print(row("Ich. Span A / B", pair(g("ICH_span_a"), g("ICH_span_b"))))

    psar_bull = g("PSAR_bull")
    psar_bear = g("PSAR_bear")
    if psar_bull is not None and not pd.isna(psar_bull):
        print(row("PSAR", f"▲ {v(psar_bull)}"))
    elif psar_bear is not None and not pd.isna(psar_bear):
        print(row("PSAR", f"▼ {v(psar_bear)}"))
    else:
        print(row("PSAR", "n/d"))

    print(section_header("MOMENTUM"))
    print(row("RSI 14", v(g("RSI_14"))))
    print(row("Stoch %K / %D", pair(g("STOCH_K"), g("STOCH_D"))))
    print(row("StochRSI %K / %D", pair(g("STOCHRSI_K"), g("STOCHRSI_D"))))
    print(row("MACD / Signal", pair(g("MACD"), g("MACD_signal"), 3)))
    print(row("MACD histogram", v(g("MACD_hist"), 3)))
    print(row("TSI / Signal", pair(g("TSI"), g("TSI_signal"))))
    print(row("CCI", v(g("CCI"))))
    print(row("Williams %R", v(g("WILLR"))))
    print(row("ROC", v(g("ROC"))))

    print(section_header("VOLATILITY"))
    print(row("BB górna / dolna", pair(g("BB_upper"), g("BB_lower"))))
    print(row("BB środkowa", v(g("BB_mid"))))
    print(row("KC górna / dolna", pair(g("KC_upper"), g("KC_lower"))))
    print(row("Donchian górna / dolna", pair(g("DC_upper"), g("DC_lower"))))
    print(row("ATR 14", v(g("ATR_14"))))

    print(section_header("VOLUME"))
    obv = g("OBV")
    obv_str = f"{obv:,.0f}" if obv is not None and not pd.isna(obv) else "n/d"
    print(row("OBV", obv_str))
    print(row("CMF", v(g("CMF"), 3)))
    print(row("MFI", v(g("MFI"))))
    print()


def signal_score(signal: dict) -> int:
    direction = 1 if signal["signal"] == "BULLISH" else -1 if signal["signal"] == "BEARISH" else 0
    return direction * STRENGTH_ORDER.get(signal["strength"], 1)


def compute_total_score(signals: list[dict]) -> int:
    return sum(signal_score(s) for s in signals)


def verdict(score: int) -> str:
    if score >= 8:
        return "SILNIE BYCZO"
    if score >= 4:
        return "BYCZO"
    if score <= -8:
        return "SILNIE NIEDŹWIEDZIO"
    if score <= -4:
        return "NIEDŹWIEDZIO"
    return "NEUTRALNIE"


def print_signals(signals: list[dict]) -> None:
    print("  SYGNAŁY")
    print(f"  {'─' * 44}")
    if not signals:
        print("  Brak wyraźnych sygnałów.")
        print()
        return
    for s in signals:
        icon = SIGNAL_ICON.get(s["signal"], "─")
        strength = s["strength"].upper()
        print(f"  {icon} [{strength:<6}] {s['indicator']:<22} {s['note']}")
    print()


def print_summary(signals: list[dict]) -> None:
    score = compute_total_score(signals)
    print(f"  {'─' * 44}")
    print(f"  SCORE: {score:+d}   →   {verdict(score)}")
    print(SEPARATOR)
    print()


def print_ticker_analysis(ticker: str, df: pd.DataFrame, signals: list[dict]) -> None:
    print_header(ticker, df)
    print_indicators(df)
    print_signals(signals)
    print_summary(signals)
