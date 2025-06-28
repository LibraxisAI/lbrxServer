"""End-to-end integration tests (in-process FastAPI test client)."""

import pytest
from httpx import AsyncClient


# Mark entire module as asyncio (pytest-asyncio v0.25+)
pytestmark = pytest.mark.asyncio


async def test_health_and_models_endpoints() -> None:  # noqa: D103
    # Import lazily so that env variables can still be tweaked by fixtures
    from src.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        # /health endpoint
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        health = resp.json()
        assert health["status"] == "healthy"

        # /models endpoint
        resp = await client.get("/api/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)