import pandas as pd

SIGNAL_ICON = {"BULLISH": "▲", "BEARISH": "▼", "NEUTRAL": "─"}
STRENGTH_ORDER = {"strong": 3, "medium": 2, "weak": 1}
COLUMN_WIDTH = 22
VALUE_WIDTH = 12
SEPARATOR = "─" * 52


def format_change(current: float, previous: float) -> str:
    if previous == 0:
        return "n/d"
    change_pct = (current - previous) / previous * 100
    sign = "+" if change_pct >= 0 else ""
    return f"{sign}{change_pct:.2f}%"


def print_header(ticker: str, df: pd.DataFrame) -> None:
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last
    date_str = pd.to_datetime(last["Date"]).strftime("%Y-%m-%d")
    change_str = format_change(last["Close"], prev["Close"])
    print(SEPARATOR)
    print(f"  {ticker.upper():<10} {last['Close']:>10.2f}   {change_str:>8}   {date_str}")
    print(SEPARATOR)


def format_indicator_row(name: str, value: float | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        formatted_value = "n/d"
    else:
        formatted_value = f"{value:.2f}"
    return f"  {name:<{COLUMN_WIDTH}} {formatted_value:>{VALUE_WIDTH}}"


def print_indicators(df: pd.DataFrame) -> None:
    last = df.iloc[-1]
    print("  WSKAŹNIKI")
    print(f"  {'─' * 34}")
    rows = [
        ("SMA 20", last.get("SMA_20")),
        ("SMA 50", last.get("SMA_50")),
        ("SMA 200", last.get("SMA_200")),
        ("RSI 14", last.get("RSI_14")),
        ("MACD", last.get("MACD")),
        ("MACD sygnał", last.get("MACD_signal")),
        ("MACD histogram", last.get("MACD_hist")),
        ("BB górna", last.get("BB_upper")),
        ("BB środkowa", last.get("BB_mid")),
        ("BB dolna", last.get("BB_lower")),
        ("ATR 14", last.get("ATR_14")),
    ]
    for name, value in rows:
        print(format_indicator_row(name, value))
    print()


def signal_score(signal: dict) -> int:
    direction = 1 if signal["signal"] == "BULLISH" else -1 if signal["signal"] == "BEARISH" else 0
    strength_weight = STRENGTH_ORDER.get(signal["strength"], 1)
    return direction * strength_weight


def compute_total_score(signals: list[dict]) -> int:
    return sum(signal_score(s) for s in signals)


def verdict(score: int) -> str:
    if score >= 5:
        return "SILNIE BYCZO"
    if score >= 2:
        return "BYCZO"
    if score <= -5:
        return "SILNIE NIEDŹWIEDZIO"
    if score <= -2:
        return "NIEDŹWIEDZIO"
    return "NEUTRALNIE"


def print_signals(signals: list[dict]) -> None:
    print("  SYGNAŁY")
    print(f"  {'─' * 34}")
    if not signals:
        print("  Brak wyraźnych sygnałów.")
        print()
        return
    for s in signals:
        icon = SIGNAL_ICON.get(s["signal"], "─")
        strength = s["strength"].upper()
        indicator = s["indicator"]
        note = s["note"]
        print(f"  {icon} [{strength:<6}] {indicator:<20} {note}")
    print()


def print_summary(signals: list[dict]) -> None:
    score = compute_total_score(signals)
    print(f"  {'─' * 34}")
    print(f"  SCORE: {score:+d}   →   {verdict(score)}")
    print(SEPARATOR)
    print()


def print_ticker_analysis(ticker: str, df: pd.DataFrame, signals: list[dict]) -> None:
    print_header(ticker, df)
    print_indicators(df)
    print_signals(signals)
    print_summary(signals)
