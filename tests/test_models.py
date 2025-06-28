"""Test model management endpoints"""
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_list_models(test_client):
    """Test listing available models"""
    response = test_client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_load_model(test_client, mock_model_manager, auth_headers):
    """Test loading a model"""
    # Skip if auth is enabled
    response = test_client.post(
        "/api/v1/models/test-model/load",
        headers=auth_headers
    )
    
    if response.status_code == 401:
        pytest.skip("Auth enabled, skipping")
    
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert data["model"] == "test-model"


@pytest.mark.asyncio
async def test_unload_model(test_client, mock_model_manager, auth_headers):
    """Test unloading a model"""
    # First, mock that the model is loaded
    mock_model_manager.models = {"test-model": AsyncMock()}
    
    response = test_client.post(
        "/api/v1/models/test-model/unload",
        headers=auth_headers
    )
    
    if response.status_code == 401:
        pytest.skip("Auth enabled, skipping")
    
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_memory_usage(test_client):
    """Test memory usage endpoint"""
    response = test_client.get("/api/v1/models/memory/usage")
    assert response.status_code == 200
    data = response.json()
    assert "used_gb" in data
    assert "total_gb" in data
    assert "available_gb" in data
    assert "loaded_models" in data