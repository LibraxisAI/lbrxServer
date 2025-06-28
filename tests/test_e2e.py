"""End-to-end integration tests (in-process FastAPI test client)."""

import pytest
from httpx import AsyncClient


# Mark entire module as asyncio (pytest-asyncio v0.25+)
pytestmark = pytest.mark.asyncio


async def test_health_and_models_endpoints() -> None:  # noqa: D103
    # Import lazily so that env variables can still be tweaked by fixtures
    import os

    # Provide safe defaults for env vars that expect JSON lists
    os.environ["API_KEYS"] = "[]"
    os.environ["ENABLE_AUTH"] = "false"
    os.environ["VOICE_SERVICES"] = "[]"

    # Monkeypatch DotEnvSettingsSource to skip reading .env files during tests
    import pydantic_settings

    original_dotenv_call = pydantic_settings.sources.DotEnvSettingsSource.__call__

    def _empty_call(self):  # noqa: D401
        return {}

    pydantic_settings.sources.DotEnvSettingsSource.__call__ = _empty_call  # type: ignore[assignment]

    # -----------------------------------------------------------------
    # Patch model_manager *before* src.main is imported to avoid MLX
    # native code execution on unsupported hardware in CI.
    # -----------------------------------------------------------------
    import types, sys

    dummy_mm = types.ModuleType("src.model_manager")

    class _DummyManager:  # noqa: D401
        models: dict[str, object] = {}
        memory_usage: dict = {"used_gb": 0, "total_gb": 0}
        current_model: str | None = None

        async def initialize(self):
            return None

        def list_available_models(self):  # noqa: D401
            return [
                {"id": "dummy-1", "loaded": False, "path": "/models/dummy-1"},
            ]

    dummy_mm.model_manager = _DummyManager()

    sys.modules["src.model_manager"] = dummy_mm
    # Ensure `import src; src.model_manager` works
    import src as src_pkg  # noqa: E402
    setattr(src_pkg, "model_manager", dummy_mm)

    from src import main as main_mod  # noqa: E402  import after patch

    app = main_mod.app

    from httpx import ASGITransport

    transport = ASGITransport(app=app, raise_app_exceptions=True)

    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        # /health endpoint
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        health = resp.json()
        assert health["status"] == "healthy"

        # /models endpoint
        resp = await client.get(
            "/api/v1/models",
            headers={"Authorization": "Bearer dummy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)