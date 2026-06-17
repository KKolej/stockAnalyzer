import pandas as pd

from stock_agents import cache
from stock_agents.cache import cache_clear, ttl_cache


def setup_function():
    cache_clear()


def test_ttl_cache_memoizes_calls():
    calls = {"n": 0}

    @ttl_cache(ttl=100)
    def expensive(x: int) -> int:
        calls["n"] += 1
        return x * 2

    assert expensive(3) == 6
    assert expensive(3) == 6
    assert calls["n"] == 1  # drugie wywołanie z cache


def test_ttl_cache_expires(monkeypatch):
    calls = {"n": 0}
    t = {"now": 1000.0}
    monkeypatch.setattr(cache.time, "monotonic", lambda: t["now"])

    @ttl_cache(ttl=10)
    def f(x: int) -> int:
        calls["n"] += 1
        return x

    f(1)
    t["now"] = 1005.0
    f(1)
    assert calls["n"] == 1  # w oknie TTL
    t["now"] = 1020.0
    f(1)
    assert calls["n"] == 2  # po wygaśnięciu


def test_dataframe_result_is_copied():
    @ttl_cache(ttl=100)
    def make_df() -> pd.DataFrame:
        return pd.DataFrame({"a": [1, 2, 3]})

    df1 = make_df()
    df1["a"] = [9, 9, 9]          # mutacja zwróconego obiektu
    df2 = make_df()
    assert list(df2["a"]) == [1, 2, 3]  # cache nietknięty


def test_cache_disabled(monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(cache, "CACHE_ENABLED", False)

    @ttl_cache(ttl=100)
    def f(x: int) -> int:
        calls["n"] += 1
        return x

    f(1)
    f(1)
    assert calls["n"] == 2  # bez cache
