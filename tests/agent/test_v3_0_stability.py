import pytest
from unittest.mock import AsyncMock, patch
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_v3_0_chained_web_task_tree():
    """
    Test a complex chained task:
    1. dirsearch finds /login.php
    2. backtracking triggers analysis of /login.php
    3. Agent runs sqlmap on /login.php
    4. confirm vuln
    """
    llm = MockLLM()
    
    # Mock MCP Client to return specific tool results
    mcp_mock = AsyncMock()
    
    def side_effect(tool, args):
        if tool == "platform_get_challenge":
            return {"id": "web-99", "description": "Scan this site: http://mock-web.local"}
        elif tool == "kali_dirsearch":
            # Simple format output
            return "200  1KB  /login.php\n404  0KB  /notfound"
        elif tool == "kali_sqlmap":
            return "Vulnerability found! GET parameter 'id' is vulnerable (Payload: ' OR 1=1 --)"
        return "Unknown tool result"

    mcp_mock.call_tool.side_effect = side_effect
    
    app = create_agent_graph(llm, mcp_client=mcp_mock)
    
    inputs = {
        "user_input": "Start scanning http://mock-web.local",
        "platform_url": "http://mock-web.local/api"
    }
    
    result = await app.ainvoke(inputs)
    
    # Verify the history trace
    history = result.get("task_history")
    tools_run = [h["tool"] for h in history]
    
    assert "platform_get_challenge" in tools_run
    assert "kali_dirsearch" in tools_run
    assert "kali_sqlmap" in tools_run
    
    # Verify result mentions vulnerability
    assert "SQL 注入已确认" in result["final_answer"]
