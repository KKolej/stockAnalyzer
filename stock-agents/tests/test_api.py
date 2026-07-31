from fastapi.testclient import TestClient

from stock_agents.api.app import app

client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_index_listuje_endpointy(self):
        resp = client.get("/")
        assert resp.status_code == 200
        endpoints = resp.json()["endpoints"]
        # kontrakt dla n8n — te ścieżki muszą być udokumentowane
        for path in ["GET /technical/{ticker}", "GET /fundamental/{ticker}",
                     "GET /macro", "GET /dcf/{ticker}", "GET /sentiment/{ticker}"]:
            assert path in endpoints


class TestOpenApiKontrakt:
    """Kontrakt schematu dla n8n — endpointy muszą istnieć w OpenAPI."""

    def test_wszystkie_sciezki_zarejestrowane(self):
        paths = client.get("/openapi.json").json()["paths"]
        expected = [
            "/technical/{ticker}", "/fundamental/{ticker}", "/screener",
            "/speculator/{ticker}", "/sentiment/{ticker}", "/dcf/{ticker}",
            "/compare", "/macro", "/analyze/{ticker}",
            "/broker/account", "/broker/positions", "/broker/orders",
        ]
        for path in expected:
            assert path in paths, f"brak {path} w OpenAPI"

    def test_endpointy_danych_maja_response_model(self):
        # response_model → schemat z $ref zamiast pustego {}
        spec = client.get("/openapi.json").json()
        for path in ["/technical/{ticker}", "/fundamental/{ticker}", "/macro",
                     "/dcf/{ticker}", "/sentiment/{ticker}"]:
            get = spec["paths"][path]["get"]
            schema = get["responses"]["200"]["content"]["application/json"]["schema"]
            assert schema, f"{path}: brak schematu odpowiedzi (response_model)"
