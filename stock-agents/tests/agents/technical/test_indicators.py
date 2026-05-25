import numpy as np
import pandas as pd
import pytest

from stock_agents.agents.technical.indicators import add_all_indicators

REQUIRED_COLUMNS = {
    "SMA_20", "SMA_50", "SMA_200",
    "RSI_14",
    "MACD", "MACD_signal", "MACD_hist",
    "BB_upper", "BB_mid", "BB_lower",
    "ATR_14",
    "OBV",
}


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    dates = pd.date_range("2022-01-01", periods=250, freq="B")
    rng = np.random.default_rng(seed=0)
    close = 50 + np.cumsum(rng.standard_normal(250) * 0.5)
    return pd.DataFrame({
        "Date": dates,
        "Open": close * 0.99,
        "High": close * 1.01,
        "Low": close * 0.98,
        "Close": close,
        "Volume": rng.integers(500_000, 2_000_000, 250).astype(float),
    })


def test_all_indicator_columns_present(sample_df: pd.DataFrame) -> None:
    result = add_all_indicators(sample_df)
    missing = REQUIRED_COLUMNS - set(result.columns)
    assert not missing, f"Brakujące kolumny: {missing}"


def test_indicator_values_are_numeric(sample_df: pd.DataFrame) -> None:
    result = add_all_indicators(sample_df)
    for col in REQUIRED_COLUMNS:
        assert pd.api.types.is_numeric_dtype(result[col]), f"Kolumna {col} nie jest numeryczna"


def test_sma200_requires_enough_rows(sample_df: pd.DataFrame) -> None:
    short_df = sample_df.iloc[:50].copy()
    result = add_all_indicators(short_df)
    assert result["SMA_200"].isna().all()
