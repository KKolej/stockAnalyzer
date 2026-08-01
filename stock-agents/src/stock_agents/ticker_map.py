GPW_COMPANIES: dict[str, str] = {
    "PKO": "PKO BP",
    "PEO": "Bank Pekao",
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
    "ALR": "Alior Bank",
    "SPL": "Santander Bank Polska",
    "KRU": "Kruk",
    "PCO": "Pepco",
    "ZAB": "Żabka",
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
# GPW tickers whose Yahoo Finance symbol differs from the Polish abbreviation
GPW_TICKER_OVERRIDES: dict[str, str] = {"KGHM": "KGH"}

# Slug in the Bankier URL != GPW abbreviation. CAUTION: /akcje/OPL is **Optopol
# Technology** (delisted from GPW), NOT Orange Polska — without this map the OPL
# sentiment pulled 2009 news about a completely different company.
BANKIER_SLUGS: dict[str, str] = {
    "OPL": "ORANGEPL",
}

# Slug of the "walor" tag on Stockwatch. The bare ticker works by default
# (/wiadomosci/walor/<ticker>); the map covers exceptions only.
STOCKWATCH_SLUGS: dict[str, str] = {}

# Name parts too generic to confirm a company's identity on a third-party page
# ("Bank" matches every bank, "Polska" matches half of GPW).
_GENERIC_NAME_TOKENS = {"bank", "banku", "polska", "polski", "grupa", "group",
                        "holding", "spolka", "spółka", "sa", "s.a."}


def ticker_to_company(ticker: str) -> str:
    upper = ticker.upper()
    if upper.endswith(US_SUFFIX):
        return upper.removesuffix(US_SUFFIX)
    return GPW_COMPANIES.get(upper, upper)


def company_identity_tokens(ticker: str) -> list[str]:
    """Company name parts usable for confirming a page's identity.

    Used by the scrapers to verify that a fetched page describes THIS company
    (e.g. the title "Optopol Technology SA" contains no part of "Orange Polska").
    """
    company = ticker_to_company(ticker)
    tokens = [t.strip(".,()").lower() for t in company.split()]
    return [t for t in tokens if len(t) >= 3 and t not in _GENERIC_NAME_TOKENS]


def is_gpw(ticker: str) -> bool:
    return not ticker.upper().endswith(US_SUFFIX)


def to_yahoo_ticker(ticker: str) -> str:
    """Converts an input ticker (e.g. PKO, CDR, TSLA.US) into a Yahoo Finance symbol."""
    upper = ticker.upper()
    if upper.endswith(US_SUFFIX):
        return upper.removesuffix(US_SUFFIX)
    base = GPW_TICKER_OVERRIDES.get(upper, upper)
    return base + GPW_SUFFIX
