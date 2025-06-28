"""Test health endpoints"""
import pytest


def test_root_endpoint(test_client):
    """Test root endpoint returns service info"""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MLX LLM Server"
    assert data["version"] == "1.0.0"
    assert data["status"] == "operational"
    assert "endpoints" in data


def test_health_endpoint(test_client):
    """Test health endpoint returns proper status"""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "memory_usage" in data
    assert "loaded_models" in data
    assert isinstance(data["loaded_models"], list)


def test_health_memory_info(test_client):
    """Test health endpoint includes memory information"""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    memory = response.json()["memory_usage"]
    assert "used_gb" in memory
    assert "total_gb" in memory
    assert "available_gb" in memory
    assert memory["total_gb"] > 0