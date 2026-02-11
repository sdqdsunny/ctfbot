import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from asas_agent.graph.workflow import create_orchestrator_graph
from asas_agent.graph.state import AgentState
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage

@pytest.mark.asyncio
async def test_fact_store_integration():
    """
    验证 Orchestrator 是否能从 ToolMessage 中提取事实并更新到 fact_store。
    """
    # 模拟 LLM
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    # 模拟第二次 invoke 返回，不需要工具调用
    mock_llm.invoke.return_value = AIMessage(content="我看到了事实，准备下一步。")
    
    app = create_orchestrator_graph(mock_llm, [])
    
    # 构造状态：上一步是 dispatch_to_agent 调用返回
    # 模拟子代理返回了事实 FACTS: {"key": "value"}
    tool_output = json.dumps({
        "status": "indeterminate",
        "reasoning": "我发现了一些线索。FACTS: {\"port_8080\": \"open\", \"vuln\": \"sqli\"}",
        "extracted_facts": {"port_8080": "open", "vuln": "sqli"},
        "flag": None
    })
    
    state = {
        "messages": [
            AIMessage(content="", tool_calls=[{"name": "dispatch_to_agent", "args": {}, "id": "call_1"}]),
            ToolMessage(content=tool_output, name="dispatch_to_agent", tool_call_id="call_1")
        ],
        "fact_store": {
            "recon": {}, "web": {}, "crypto": {}, "reverse": {}, "common": {}
        }
    }
    
    # 获取 orchestrator 节点
    # 注意：create_orchestrator_graph 返回的是编译后的 graph，我们需要通过 node 名访问
    # 或者直接调用 workflow 中定义的 orchestrator_node
    
    # 重新查找 orchestrator_node (因为它在 create_orchestrator_graph 闭包内，我们直接模拟调用)
    # 我们需要手动抓取闭包里的 node 有点难，不如直接跑一次 graph 抽取的逻辑
    
    result = await app.ainvoke(state)
    
    # 验证 fact_store 是否已更新
    final_fact_store = result["fact_store"]
    assert final_fact_store["common"]["port_8080"] == "open"
    assert final_fact_store["common"]["vuln"] == "sqli"
    
    # 验证发送给 LLM 的 SystemMessage 是否包含事实集
    # 我们检查 mock_llm.invoke 的调用参数
    sent_messages = mock_llm.invoke.call_args[0][0]
    system_msg = next(m for m in sent_messages if isinstance(m, SystemMessage))
    assert "[当前全局事实仓库]" in system_msg.content
    assert "port_8080" in system_msg.content
    
    print("\n✅ Fact Store 集成测试通过！事实已成功从工具返回合并到全局库并注入下一次推理。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fact_store_integration())
