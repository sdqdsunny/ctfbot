import pytest
from unittest.mock import AsyncMock, MagicMock
from asas_agent.graph.nodes import AgentNodes
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_nodes_plan_actions_crypto():
    llm = MockLLM()
    mcp_client = AsyncMock()
    
    nodes = AgentNodes(llm, mcp_client)
    
    # Test with colon
    state_input = {"user_input": "decode: dGVzdA==", "task_understanding": "crypto_decode"}
    new_state = await nodes.plan_actions(state_input)
    assert new_state["planned_tool"] == "crypto_decode"
    assert new_state["tool_args"]["content"] == "dGVzdA=="

@pytest.mark.asyncio
async def test_nodes_execute_tool():
    llm = MockLLM()
    mcp_client = AsyncMock()
    mcp_client.call_tool.return_value = "Decoded Content"
    
    nodes = AgentNodes(llm, mcp_client)
    
    state = {
        "planned_tool": "crypto_decode",
        "tool_args": {"content": "dGVzdA=="}
    }
    
    new_state = await nodes.execute_tool(state)
    assert new_state["tool_result"] == "Decoded Content"
