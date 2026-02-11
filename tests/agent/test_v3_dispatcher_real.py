import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from asas_agent.graph.dispatcher import dispatch_to_agent
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_dispatch_to_agent_real_logic():
    """
    测试 dispatch_to_agent 是否能正确加载配置、实例化 LLM 并调用子 Agent。
    """
    # 模拟配置
    mock_config = {
        "orchestrator": {"provider": "anthropic", "model": "test-orch"},
        "agents": {
            "crypto": {"provider": "anthropic", "model": "test-crypto"}
        }
    }
    
    # 模拟依赖项
    with patch("asas_agent.utils.config.ConfigLoader.load_config", return_value=mock_config), \
         patch("asas_agent.graph.dispatcher.create_llm") as mock_create_llm, \
         patch("asas_agent.graph.dispatcher.AGENT_CREATORS") as mock_creators:
        
        # 1. 模拟子 Agent 图
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [AIMessage(content="分析完毕。解码结果显示 flag 是 flag{internal_agent_success}")]
        })
        
        # 2. 模拟 AGENT_CREATORS 包含 crypto 并返回 Creator
        mock_creators.__contains__.return_value = True
        mock_creators.__getitem__.return_value = lambda llm, tools: mock_graph
        
        # 执行调度工具
        result_json = await dispatch_to_agent.ainvoke({
            "agent_type": "crypto",
            "task": "请尝试解码：SGVsbG8=",
            "platform_context": {"challenge_id": "123", "platform_url": "http://ctf.test"}
        })
        
        # 验证结果
        result = json.loads(result_json)
        if result["status"] == "failure":
            print(f"DEBUG: result={result}")
        assert result["status"] == "success"
        assert result["flag"] == "flag{internal_agent_success}"
        assert "分析完毕" in result["reasoning"]
        
        # 验证 LLM 实例化时使用了正确的配置
        mock_create_llm.assert_called_once()
        call_args = mock_create_llm.call_args[0][0]
        assert call_args["model"] == "test-crypto"
        
        print("\n✅ Dispatcher 真实逻辑测试通过！已成功模拟配置加载与子 Agent 链式调用。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_dispatch_to_agent_real_logic())
