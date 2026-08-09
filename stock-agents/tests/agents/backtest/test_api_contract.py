from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from stock_agents.api.app import app

client = TestClient(app)


def test_endpoint_registered_in_openapi() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/backtest/{ticker}" in paths


def test_listed_on_index_for_n8n() -> None:
    assert "GET /backtest/{ticker}" in client.get("/").json()["endpoints"]


def test_short_history_returns_a_reason_not_a_crash() -> None:
    with patch("stock_agents.agents.backtest.agent.get_data") as fake:
        fake.return_value = {"ticker": "XYZ", "error": "Za krótka historia: 40 sesji"}
        with patch("stock_agents.api.routes.backtest.get_data", fake):
            resp = client.get("/backtest/XYZ")
    assert resp.status_code == 200
    assert "Za krótka historia" in resp.json()["error"]


def test_response_keeps_the_fields_n8n_reads() -> None:
    payload = {
        "ticker": "CDR",
        "is_backtested": True,
        "period": {"from": "2019-01-02", "to": "2026-08-07", "sessions": 1854, "years": 7.36},
        "horizons_days": [5, 10, 21, 63],
        "min_sample_for_verdict": 20,
        "signals": [
            {
                "key": "rsi_oversold_30",
                "note": "RSI spadł poniżej 30 (wyprzedanie)",
                "direction": "bullish",
                "occurrences": 22,
                "sessions_since_last": 43,
                "horizons": [
                    {
                        "horizon_days": 21,
                        "sample_size": 22,
                        "effective_sample": 20,
                        "hit_rate_pct": 59.1,
                        "baseline_hit_rate_pct": 54.0,
                        "edge_pp": 5.1,
                        "mean_return_pct": 3.2,
                        "median_return_pct": 2.0,
                        "baseline_mean_return_pct": 1.5,
                        "excess_return_pct": 1.69,
                        "worst_return_pct": -20.0,
                        "best_return_pct": 30.0,
                        "t_stat": 1.2,
                        "reliable": False,
                        "reading": "bez przewagi ponad szum",
                    }
                ],
            }
        ],
        "active_signals": [],
        "reliable_signals": [],
        "caveats": ["Zwroty bez kosztów transakcyjnych."],
    }
    with patch("stock_agents.api.routes.backtest.get_data", return_value=payload):
        body = client.get("/backtest/CDR").json()

    assert body["is_backtested"] is True
    assert body["period"]["from"] == "2019-01-02"
    horizon = body["signals"][0]["horizons"][0]
    # The consumer decides on these three: measured edge, sample and reliability flag.
    assert horizon["excess_return_pct"] == 1.69
    assert horizon["sample_size"] == 22
    assert horizon["reliable"] is False
    assert body["caveats"]
