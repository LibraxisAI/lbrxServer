"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_model_manager():
    """Mock model manager for tests"""
    manager = AsyncMock()
    manager.models = {}
    manager.memory_usage = {"used_gb": 0, "total_gb": 32, "available_gb": 32}
    manager.load_model = AsyncMock(return_value=True)
    manager.unload_model = AsyncMock(return_value=True)
    manager.generate = AsyncMock(return_value="Test response")
    return manager


@pytest.fixture
def mock_config():
    """Mock configuration for tests"""
    from unittest.mock import MagicMock
    config = MagicMock()
    config.api_prefix = "/api/v1"
    config.enable_auth = False
    config.enable_metrics = False
    config.host = "0.0.0.0"
    config.port = 9123
    config.default_model = "test-model"
    return config


@pytest.fixture
def test_client(mock_model_manager, mock_config, monkeypatch):
    """Create test client with mocked dependencies"""
    # Mock the imports
    monkeypatch.setattr("src.model_manager.model_manager", mock_model_manager)
    monkeypatch.setattr("src.config.config", mock_config)
    
    # Import app after mocking
    from src.main import app
    
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Auth headers for testing"""
    return {"Authorization": "Bearer test-api-key"}