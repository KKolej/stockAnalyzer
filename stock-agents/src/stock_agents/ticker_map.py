GPW_COMPANIES: dict[str, str] = {
    "PKO": "PKO BP",
    "CDR": "CD Projekt",
    "KGHM": "KGHM",
    "PZU": "PZU",
    "PKN": "PKN Orlen",
    "PGE": "PGE",
    "LPP": "LPP",
    "ALE": "Allegro",
    "DNP": "Dino Polska",
    "MBK": "mBank",
    "OPL": "Orange Polska",
    "CPS": "Cyfrowy Polsat",
    "JSW": "JSW",
    "CCC": "CCC",
    "EUR": "Eurocash",
    "GTC": "GTC",
    "BDX": "Budimex",
    "TPE": "Tauron",
    "ENG": "Energa",
}

US_SUFFIX = ".US"
GPW_SUFFIX = ".WA"
# Tickery GPW których symbol w Yahoo Finance różni się od polskiego skrótu
GPW_TICKER_OVERRIDES: dict[str, str] = {"KGHM": "KGH"}


def ticker_to_company(ticker: str) -> str:
    upper = ticker.upper()
    if upper.endswith(US_SUFFIX):
        return upper.removesuffix(US_SUFFIX)
    return GPW_COMPANIES.get(upper, upper)


def is_gpw(ticker: str) -> bool:
    return not ticker.upper().endswith(US_SUFFIX)


def to_yahoo_ticker(ticker: str) -> str:
    """Konwertuje ticker wejściowy (np. PKO, CDR, TSLA.US) na symbol Yahoo Finance."""
    upper = ticker.upper()
    if upper.endswith(US_SUFFIX):
        return upper.removesuffix(US_SUFFIX)
    base = GPW_TICKER_OVERRIDES.get(upper, upper)
    return base + GPW_SUFFIX
