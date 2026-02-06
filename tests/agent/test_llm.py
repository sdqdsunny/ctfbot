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
