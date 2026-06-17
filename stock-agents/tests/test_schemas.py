from stock_agents.api.schemas import FundamentalResponse, TechnicalResponse


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


def test_schemas_present_in_openapi():
    from stock_agents.api.app import app
    schemas = app.openapi()["components"]["schemas"]
    assert "TechnicalResponse" in schemas
    assert "FundamentalResponse" in schemas
    ref = app.openapi()["paths"]["/technical/{ticker}"]["get"]["responses"]["200"]
    assert ref["content"]["application/json"]["schema"]["$ref"].endswith("TechnicalResponse")
