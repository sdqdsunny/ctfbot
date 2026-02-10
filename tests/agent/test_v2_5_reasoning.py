import pytest
from unittest.mock import AsyncMock, patch
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_v2_5_full_reverse_reasoning_loop_mock():
    """
    Test v2.5 loop with Mocked MCP
    """
    llm = MockLLM()
    
    # Mock MCP Client
    mcp_mock = AsyncMock()
    
    def side_effect(tool, args):
        if tool == "platform_get_challenge":
            return {"id": "rev-456", "description": "Please decompile this binary and find the flag."}
        elif tool == "reverse_ghidra_decompile":
            return {"main": "void main() { char flag[] = {0x0e, ...}; }"}
        elif tool == "misc_run_python":
            return "flag{mock_reverse_success}"
        elif tool == "platform_submit_flag":
            return "Correct!"
        return "Unknown tool result"

    mcp_mock.call_tool.side_effect = side_effect
    
    with patch('asas_agent.mcp_client.client.MCPToolClient', return_value=mcp_mock):
        app = create_agent_graph(llm)
        
        inputs = {
            "user_input": "Start reverse task",
            "platform_url": "http://mock-ctf.local/api/v1/challenges/456",
            "platform_token": "mock-token"
        }
        
        result = await app.ainvoke(inputs)
        
        assert "Flag Submitted" in result["final_answer"]
        assert "Correct!" in result["final_answer"]
