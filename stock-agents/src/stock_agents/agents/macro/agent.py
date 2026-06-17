from __future__ import annotations

from .fetcher import fetch
from .models import MacroData
from .printer import print_macro


def get_data() -> MacroData:
    return fetch()


def run() -> None:
    print_macro(get_data())
