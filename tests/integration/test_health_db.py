import pytest
from sqlalchemy import text

from app.core.database import engine


@pytest.mark.integration
def test_database_health_returns_ok(client):
    response = client.get("/api/v1/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.integration
def test_database_reachable():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1
