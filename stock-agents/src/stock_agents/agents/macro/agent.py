from __future__ import annotations

from .fetcher import fetch
from .printer import print_macro


def run() -> None:
    data = fetch()
    print_macro(data)
