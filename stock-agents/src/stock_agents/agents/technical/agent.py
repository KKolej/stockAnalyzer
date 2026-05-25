from stock_agents.agents.technical.fetcher import FetchError, fetch_ohlcv
from stock_agents.agents.technical.indicators import add_all_indicators
from stock_agents.agents.technical.printer import print_ticker_analysis
from stock_agents.agents.technical.signals import generate_signals


def analyze_ticker(ticker: str, days_back: int) -> None:
    try:
        df = fetch_ohlcv(ticker, days_back)
        df = add_all_indicators(df)
        signals = generate_signals(df)
        print_ticker_analysis(ticker, df, signals)
    except FetchError as exc:
        print(f"[BŁĄD] {ticker}: {exc}")


def run_technical_agent(tickers: list[str], days_back: int) -> None:
    for ticker in tickers:
        analyze_ticker(ticker, days_back)
