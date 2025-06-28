"""Test configuration module"""
import pytest
from pathlib import Path
import os


def test_model_config_import():
    """Test that model config can be imported"""
    from src.model_config import ModelConfig, ModelType, MODEL_ALIASES
    
    assert ModelConfig is not None
    assert ModelType is not None
    assert isinstance(MODEL_ALIASES, dict)


def test_default_model_exists():
    """Test that default model is configured"""
    from src.model_config import ModelConfig, MODEL_ALIASES
    
    default_alias = MODEL_ALIASES.get("default")
    assert default_alias is not None
    
    model_config = ModelConfig.get_model_config(default_alias)
    assert model_config is not None
    assert "id" in model_config
    assert "type" in model_config
    assert "memory_gb" in model_config


def test_qwen_model_configured():
    """Test that Qwen3-14b model is properly configured"""
    from src.model_config import ModelConfig
    
    model_config = ModelConfig.get_model_config("qwen3-14b")
    assert model_config is not None
    assert model_config["id"] == "LibraxisAI/Qwen3-14b-MLX-Q5"
    assert model_config["memory_gb"] == 10
    assert model_config["auto_load"] == True
    assert model_config["priority"] == 1


def test_model_aliases():
    """Test model aliases work correctly"""
    from src.model_config import ModelConfig, MODEL_ALIASES
    
    # Test that aliases resolve correctly
    assert MODEL_ALIASES["default"] == "qwen3-14b"
    assert MODEL_ALIASES["qwen"] == "qwen3-14b"
    assert MODEL_ALIASES["qwen3"] == "qwen3-14b"
    
    # Test alias resolution
    config_by_alias = ModelConfig.get_model_config("qwen")
    config_direct = ModelConfig.get_model_config("qwen3-14b")
    assert config_by_alias == config_direct


def test_memory_estimation():
    """Test memory usage estimation"""
    from src.model_config import ModelConfig
    
    # Test single model
    memory = ModelConfig.estimate_memory_usage(["qwen3-14b"])
    assert memory == 10
    
    # Test multiple models
    memory = ModelConfig.estimate_memory_usage(["qwen3-14b", "llama-3.2-3b"])
    assert memory == 14  # 10 + 4