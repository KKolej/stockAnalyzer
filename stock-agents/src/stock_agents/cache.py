"""Simple, thread-safe in-memory TTL cache.

Essential for a cloud deployment: yfinance and scraping are slow and rate-limited.
The cache cuts the number of requests and speeds up the aggregate endpoints.

pandas objects are copied on write and on read — so mutating a returned DataFrame
(e.g. adding indicators) does not corrupt the cache entry.
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

DEFAULT_TTL = int(os.getenv("CACHE_TTL", "900"))  # seconds (15 min by default)
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "1") != "0"

_CACHE: dict[Any, tuple[float, Any]] = {}
_LOCK = threading.Lock()


def _copy(value: Any) -> Any:
    if isinstance(value, pd.DataFrame | pd.Series):
        return value.copy()
    return value


def ttl_cache(ttl: int = DEFAULT_TTL) -> Callable[[F], F]:
    """Decorator caching a function result for `ttl` seconds (key = arguments)."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not CACHE_ENABLED:
                return fn(*args, **kwargs)
            key = (fn.__module__, fn.__qualname__, args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            with _LOCK:
                hit = _CACHE.get(key)
                if hit is not None and now < hit[0]:
                    return _copy(hit[1])
            result = fn(*args, **kwargs)
            with _LOCK:
                # drop expired entries so the cache does not grow without bound
                expired = [k for k, (exp, _) in _CACHE.items() if now >= exp]
                for k in expired:
                    del _CACHE[k]
                _CACHE[key] = (now + ttl, _copy(result))
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def cache_clear() -> None:
    with _LOCK:
        _CACHE.clear()


def cache_stats() -> dict[str, int]:
    with _LOCK:
        return {"entries": len(_CACHE)}
