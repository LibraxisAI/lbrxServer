"""Test model routing functionality"""
import pytest
from src.model_router import ModelRouter


class TestModelRouter:
    """Test cases for model routing"""
    
    def test_default_routing(self):
        """Test default model selection"""
        model = ModelRouter.get_model_for_request()
        assert model == "default"
    
    def test_explicit_model_request(self):
        """Test explicit model request takes precedence"""
        model = ModelRouter.get_model_for_request(
            service="vista",
            requested_model="custom-model"
        )
        assert model == "custom-model"
    
    def test_service_based_routing(self):
        """Test service-specific model routing"""
        # VISTA should get Qwen3-14b
        model = ModelRouter.get_model_for_request(service="vista")
        assert model == "qwen3-14b"
        
        # forkmeASAPp should get DeepSeek
        model = ModelRouter.get_model_for_request(service="forkmeASAPp")
        assert model == "deepseek-coder"
        
        # lbrxvoice should get Phi-3
        model = ModelRouter.get_model_for_request(service="lbrxvoice")
        assert model == "phi-3"
    
    def test_api_key_service_extraction(self):
        """Test extracting service from API key"""
        # Test various prefixes
        assert ModelRouter.extract_service_from_api_key("vista_xxxxx") == "vista"
        assert ModelRouter.extract_service_from_api_key("whisp_xxxxx") == "whisplbrx"
        assert ModelRouter.extract_service_from_api_key("fork_xxxxx") == "forkmeASAPp"
        assert ModelRouter.extract_service_from_api_key("data_xxxxx") == "anydatanext"
        assert ModelRouter.extract_service_from_api_key("voice_xxxxx") == "lbrxvoice"
        
        # Test with Bearer prefix
        assert ModelRouter.extract_service_from_api_key("Bearer vista_xxxxx") == "vista"
        
        # Test unknown prefix
        assert ModelRouter.extract_service_from_api_key("unknown_xxxxx") is None
        assert ModelRouter.extract_service_from_api_key("noprefix") is None
    
    def test_fallback_chain(self):
        """Test model fallback chain"""
        assert ModelRouter.get_fallback_model("qwen3-14b") == "mistral-7b"
        assert ModelRouter.get_fallback_model("mistral-7b") == "llama-3.2-3b"
        assert ModelRouter.get_fallback_model("llama-3.2-3b") is None
    
    def test_user_override(self):
        """Test user-specific model override"""
        # Add a test user override
        ModelRouter.USER_OVERRIDES["test@example.com"] = {"*": "premium-model"}
        
        model = ModelRouter.get_model_for_request(
            service="vista",
            user="test@example.com"
        )
        assert model == "premium-model"
        
        # Clean up
        del ModelRouter.USER_OVERRIDES["test@example.com"]