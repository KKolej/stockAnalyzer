from stock_agents.api.schemas import (
    CompareResponse,
    DCFResponse,
    FundamentalResponse,
    MacroResponse,
    ScreenerResponse,
    SentimentResponse,
    SpeculatorResponse,
    TechnicalResponse,
)


def test_technical_preserves_extra_fields():
    # nowe pole agenta nie może zniknąć (extra="allow")
    m = TechnicalResponse.model_validate(
        {"ticker": "CDR", "score": 5, "NOWE_POLE": 123, "risk": {"sharpe": 1.2, "EXTRA": 9}}
    )
    d = m.model_dump()
    assert d["NOWE_POLE"] == 123
    assert d["risk"]["EXTRA"] == 9
    assert d["risk"]["sharpe"] == 1.2


def test_technical_error_only_response_validates():
    # ścieżka błędu agenta: tylko ticker + error
    m = TechnicalResponse.model_validate({"ticker": "BADTICKER", "error": "Brak danych"})
    assert m.ticker == "BADTICKER"
    assert m.error == "Brak danych"
    assert m.price is None
    assert m.signals == []


def test_fundamental_response_shape():
    m = FundamentalResponse.model_validate({
        "data": {"ticker": "ALE", "company": "Allegro", "pe_trailing": 17.8, "EXTRA_METRIC": 1},
        "signals": [{"indicator": "ROE", "signal": "BULLISH", "strength": "weak", "note": "ok"}],
    })
    assert m.data.pe_trailing == 17.8
    assert m.data.model_dump()["EXTRA_METRIC"] == 1
    assert m.signals[0].signal == "BULLISH"


def test_dcf_error_and_extra():
    m = DCFResponse.model_validate({"ticker": "PKO", "error": "Brak FCF", "NEW": 1})
    assert m.error == "Brak FCF"
    assert m.scenarios == []
    assert m.model_dump()["NEW"] == 1


def test_speculator_shape():
    m = SpeculatorResponse.model_validate({
        "ticker": "CDR",
        "patterns": [{
            "name": "seasonal", "direction": "UP", "strength": "medium",
            "probability": 0.6, "sample_size": 30, "EXTRA": 1,
        }],
    })
    assert m.patterns[0].direction == "UP"
    assert m.patterns[0].model_dump()["EXTRA"] == 1


def test_screener_shape():
    m = ScreenerResponse.model_validate({
        "total": 2, "matched": 1, "filters": {"pe_max": 15.0},
        "rows": [{"ticker": "PKO", "pe": 8.0}],
        "errors": [{"ticker": "XXX", "error": "brak"}],
    })
    assert m.matched == 1
    assert m.rows[0].pe == 8.0
    assert m.errors[0].error == "brak"


def test_sentiment_computed_fields_preserved():
    # pola z @property serializera muszą trafić do kontraktu
    m = SentimentResponse.model_validate({
        "ticker": "PKO", "company": "PKO", "mode": "keyword",
        "results": [{"name": "bankier", "mentions": [], "available": True, "bullish_count": 0}],
        "total_mentions": 0, "overall_score": 0.0, "overall_label": "NEUTRAL",
    })
    assert m.overall_label == "NEUTRAL"
    assert m.results[0].available is True


def test_macro_shape():
    m = MacroResponse.model_validate({
        "as_of": "2026-06-28",
        "fx": [{"code": "USD", "name": "Dolar", "rate": 4.0, "date": "2026-06-28"}],
        "cpi_change_pct": 3.1, "errors": [],
    })
    assert m.fx[0].code == "USD"
    assert m.cpi_change_pct == 3.1


def test_compare_shape():
    m = CompareResponse.model_validate({
        "tickers": ["PKO", "CDR"],
        "data": [{"ticker": "PKO", "pe": 8.0, "EXTRA": 1}],
    })
    assert m.data[0].pe == 8.0
    assert m.data[0].model_dump()["EXTRA"] == 1


def test_schemas_present_in_openapi():
    from stock_agents.api.app import app
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "TechnicalResponse", "FundamentalResponse", "DCFResponse",
        "SpeculatorResponse", "ScreenerResponse", "SentimentResponse",
        "MacroResponse", "CompareResponse",
    ):
        assert name in schemas, name
    paths = app.openapi()["paths"]
    for path, model in (
        ("/technical/{ticker}", "TechnicalResponse"),
        ("/dcf/{ticker}", "DCFResponse"),
        ("/speculator/{ticker}", "SpeculatorResponse"),
        ("/sentiment/{ticker}", "SentimentResponse"),
        ("/macro", "MacroResponse"),
        ("/compare", "CompareResponse"),
        ("/screener", "ScreenerResponse"),
    ):
        ref = paths[path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        assert ref.endswith(model), (path, ref)
