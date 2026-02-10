import pytest
import asyncio
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM
from unittest.mock import patch, Mock

@pytest.mark.asyncio
@patch("requests.get")
@patch("requests.post")
async def test_platform_full_loop_mock(mock_post, mock_get):
    """
    Test the full loop: 
    1. Fetch challenge from mock platform
    2. Understand description -> crypto intent
    3. Decode flag
    4. Auto-submit flag back to platform
    """
    llm = MockLLM()
    app = create_agent_graph(llm)

    # Mock responses
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": {"name": "Test Chall", "description": "flag is encoded in base64: ZmxhZ3tzeW1ib2xpY19leGVjdXRpb259"}}
    mock_get.return_value = mock_resp
    
    # Mock submit response
    mock_post_resp = Mock()
    mock_post_resp.status_code = 200 
    mock_post_resp.json.return_value = {"success": True, "data": {"status": "correct"}}
    mock_post.return_value = mock_post_resp
    
    # 模拟从平台 URL 开始
    inputs = {
        "user_input": "Start task",
        "platform_url": "http://mock-ctf.local/api/v1/challenges/123",
        "platform_token": "mock-token"
    }
    
    # 执行图
    # 预期路径: 
    # start -> understand (intent=platform_fetch) 
    # -> plan (tool=platform_get_challenge) 
    # -> execute (fetches mock desc)
    # -> understand (intent=crypto_decode)
    # -> plan (tool=crypto_decode)
    # -> execute (decodes flag)
    # -> plan (intet: detects flag -> tool=platform_submit_flag)
    # -> execute (submits)
    # -> format -> END
    
    result = await app.ainvoke(inputs)
    
    # 验证最终结果
    assert "Flag Submitted" in result["final_answer"]
    assert "Correct!" in result["final_answer"]
    assert result["challenge_id"] == "123"
