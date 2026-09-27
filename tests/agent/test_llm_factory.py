import pytest
from unittest.mock import patch, MagicMock
from langchain_anthropic import ChatAnthropic
from asas_agent.llm.factory import create_llm, LMStudioLLM

def test_create_llm_anthropic():
    config = {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20240620",
        "api_key": "fake-key"
    }
    llm = create_llm(config)
    assert isinstance(llm, ChatAnthropic)
    assert llm.model == config["model"]

def test_create_llm_lmstudio():
    config = {
        "provider": "lmstudio",
        "model": "gpt-oss-20b",
        "base_url": "http://localhost:1234/v1"
    }
    llm = create_llm(config)
    assert isinstance(llm, LMStudioLLM)
    assert llm.model_name == config["model"]
    assert llm.base_url == config["base_url"]

def test_create_llm_invalid_provider():
    config = {
        "provider": "unknown",
        "model": "test"
    }
    with pytest.raises(ValueError, match="Unsupported provider"):
        create_llm(config)
