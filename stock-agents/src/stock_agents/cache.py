"""Prosty, wątkowo-bezpieczny cache TTL w pamięci.

Niezbędny dla wdrożenia w chmurze: yfinance/scraping są wolne i podatne na
rate-limity. Cache redukuje liczbę zapytań i przyspiesza zbiorcze endpointy.

Obiekty pandas są kopiowane przy zapisie i odczycie — dzięki temu mutacja
zwróconego DataFrame (np. dodanie wskaźników) nie psuje wpisu w cache.
"""
from __future__ import annotations

import functools
import os
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

import pandas as pd

F = TypeVar("F", bound=Callable[..., Any])

DEFAULT_TTL = int(os.getenv("CACHE_TTL", "900"))  # sekundy (domyślnie 15 min)
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "1") != "0"

_CACHE: dict[Any, tuple[float, Any]] = {}
_LOCK = threading.Lock()


def _copy(value: Any) -> Any:
    if isinstance(value, pd.DataFrame | pd.Series):
        return value.copy()
    return value


def ttl_cache(ttl: int = DEFAULT_TTL) -> Callable[[F], F]:
    """Dekorator cache'ujący wynik funkcji na `ttl` sekund (klucz = argumenty)."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not CACHE_ENABLED:
                return fn(*args, **kwargs)
            key = (fn.__module__, fn.__qualname__, args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            with _LOCK:
                hit = _CACHE.get(key)
                if hit is not None and now - hit[0] < ttl:
                    return _copy(hit[1])
            result = fn(*args, **kwargs)
            with _LOCK:
                _CACHE[key] = (now, _copy(result))
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def cache_clear() -> None:
    with _LOCK:
        _CACHE.clear()


def cache_stats() -> dict[str, int]:
    with _LOCK:
        return {"entries": len(_CACHE)}
