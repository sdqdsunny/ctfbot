import pytest
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_agent_zeroclaw_intent():
    llm = MockLLM()
    mcp_mock = AsyncMock()
    mcp_mock.call_tool.return_value = "✅ ZeroClaw browser launched for kali at http://192.168.1.50:6080/vnc.html"
    
    app = create_agent_graph(llm, mcp_client=mcp_mock)
    
    inputs = {"user_input": "请使用 GUI 访问 Kali 虚拟机查看浏览器"}
    result = await app.ainvoke(inputs)
    
    assert "ZeroClaw browser launched" in result["final_answer"]
    mcp_mock.call_tool.assert_called_with("invoke_zeroclaw_vnc", {"vm_name": "kali"})
