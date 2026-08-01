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
# Tickery GPW których symbol w Yahoo Finance różni się od polskiego skrótu
GPW_TICKER_OVERRIDES: dict[str, str] = {"KGHM": "KGH"}

# Slug w URL Bankiera ≠ skrót GPW. UWAGA: /akcje/OPL to **Optopol Technology**
# (spółka wycofana z GPW), NIE Orange Polska — bez tej mapy sentyment OPL
# zaciągał newsy z 2009 r. o zupełnie innej spółce.
BANKIER_SLUGS: dict[str, str] = {
    "OPL": "ORANGEPL",
}

# Slug tagu „walor" na Stockwatch. Domyślnie działa sam ticker
# (/wiadomosci/walor/<ticker>), mapa jest tylko dla wyjątków.
STOCKWATCH_SLUGS: dict[str, str] = {}

# Człony nazw zbyt ogólne, by potwierdzić tożsamość spółki na obcej stronie
# ("Bank" pasuje do każdego banku, "Polska" do połowy GPW).
_GENERIC_NAME_TOKENS = {"bank", "banku", "polska", "polski", "grupa", "group",
                        "holding", "spolka", "spółka", "sa", "s.a."}


def ticker_to_company(ticker: str) -> str:
    upper = ticker.upper()
    if upper.endswith(US_SUFFIX):
        return upper.removesuffix(US_SUFFIX)
    return GPW_COMPANIES.get(upper, upper)


def company_identity_tokens(ticker: str) -> list[str]:
    """Człony nazwy spółki nadające się do potwierdzenia tożsamości strony.

    Używane przez scrapery do weryfikacji, że pobrana strona dotyczy TEJ spółki
    (np. tytuł „Optopol Technology SA" nie zawiera żadnego członu „Orange Polska").
    """
    company = ticker_to_company(ticker)
    tokens = [t.strip(".,()").lower() for t in company.split()]
    return [t for t in tokens if len(t) >= 3 and t not in _GENERIC_NAME_TOKENS]


def is_gpw(ticker: str) -> bool:
    return not ticker.upper().endswith(US_SUFFIX)


def to_yahoo_ticker(ticker: str) -> str:
    """Konwertuje ticker wejściowy (np. PKO, CDR, TSLA.US) na symbol Yahoo Finance."""
    upper = ticker.upper()
    if upper.endswith(US_SUFFIX):
        return upper.removesuffix(US_SUFFIX)
    base = GPW_TICKER_OVERRIDES.get(upper, upper)
    return base + GPW_SUFFIX
