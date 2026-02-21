import pytest
from unittest.mock import AsyncMock
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_v2_5_full_reverse_reasoning_loop_mock():
    """
    Test v2.5 loop with Mocked MCP.
    Flow: platform_fetch → decompile → find flag
    """
    llm = MockLLM()
    
    # Mock MCP Client
    mcp_mock = AsyncMock()
    
    def side_effect(tool, args):
        if tool == "platform_get_challenge":
            return {"id": "rev-456", "description": "Please decompile this binary and find the flag."}
        elif tool == "reverse_ghidra_decompile":
            return {"main": "void main() { printf(\"flag{mock_reverse_success}\"); }"}
        elif tool == "sandbox_execute":
            return "flag{mock_reverse_success}"
        elif tool == "platform_submit_flag":
            return "Correct!"
        return "Unknown tool result"

    mcp_mock.call_tool.side_effect = side_effect
    
    app = create_agent_graph(llm, mcp_client=mcp_mock)
    
    inputs = {
        "user_input": "Start reverse task",
        "platform_url": "http://mock-ctf.local/api/v1/challenges/456",
        "platform_token": "mock-token"
    }
    
    result = await app.ainvoke(inputs)
    
    # Verify at least platform_fetch + decompile happened
    history = result.get("task_history", [])
    tools_run = [h["tool"] for h in history]
    assert "platform_get_challenge" in tools_run
    # The chain should continue to decompile after getting challenge desc
    assert "reverse_ghidra_decompile" in tools_run
    # Final answer should contain flag or decompile result
    assert "flag{" in result["final_answer"].lower() or "decompile" in result["final_answer"].lower() or "main" in result["final_answer"].lower()
