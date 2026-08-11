def test_health_returns_ok(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_response_model_shape(client):
    response = client.get("/api/v1/health")

    assert set(response.json().keys()) == {"status"}


def test_openapi_schema_available():
    from app.main import app

    schema = app.openapi()

    assert schema["info"]["title"] == "Company Management System"
    assert "/api/v1/health" in schema["paths"]
