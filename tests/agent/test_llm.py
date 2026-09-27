import pytest
from asas_agent.llm.mock import MockLLM

def test_mock_llm_crypto_decode():
    llm = MockLLM()
    messages = [{"role": "user", "content": "请解码这段 Base64: SGVsbG8="}]
    response = llm.chat(messages)
    assert "crypto_decode" in response

def test_mock_llm_recon_scan():
    llm = MockLLM()
    messages = [{"role": "user", "content": "扫描 IP 127.0.0.1"}]
    response = llm.chat(messages)
    assert "recon_scan" in response

def test_mock_llm_unknown():
    llm = MockLLM()
    messages = [{"role": "user", "content": "你好"}]
    response = llm.chat(messages)
    assert "unknown" in response

from unittest.mock import MagicMock, patch
from asas_agent.llm.claude import ClaudeLLM

def test_claude_llm_call():
    with patch("anthropic.Anthropic") as MockAnthropic:
        # User auth check
        mock_client = MockAnthropic.return_value
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response from Claude")]
        mock_client.messages.create.return_value = mock_message
        
        llm = ClaudeLLM(api_key="fake-key")
        messages = [{"role": "user", "content": "Hello"}]
        response = llm.chat(messages)
        
        assert response == "Response from Claude"
        mock_client.messages.create.assert_called_once()
