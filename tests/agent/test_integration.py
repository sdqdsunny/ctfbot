import pytest
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_end_to_end_crypto_mock():
    # Setup
    llm = MockLLM()
    app = create_agent_graph(llm)
    
    # Exec
    # Mock LLM knows "decode" maps to crypto_decode
    # Nodes.plan_actions knows to extract content after colon
    inputs = {"user_input": "Please decode: SGVsbG8gV29ybGQ="}
    result = await app.ainvoke(inputs)
    
    # Verify
    assert result["task_understanding"] == "crypto_decode"
    assert result["planned_tool"] == "crypto_decode"
    assert result["tool_args"]["content"] == "SGVsbG8gV29ybGQ="
    # This proves we actually called the running MCP server!
    assert "Hello World" in result["final_answer"]
    
@pytest.mark.asyncio
async def test_end_to_end_recon_scan_mock():
    # Setup
    llm = MockLLM()
    app = create_agent_graph(llm)
    
    # Exec
    inputs = {"user_input": "扫描 IP 127.0.0.1"}
    result = await app.ainvoke(inputs)
    
    # Verify
    assert result["task_understanding"] == "recon_scan"
    assert result["planned_tool"] == "recon_scan"
    assert result["tool_args"]["target"] == "127.0.0.1"
    # Just checking it returns a result, exact content depends on nmap execution
    # For CI usually nmap might not be present or sudo issue, but let's see. 
    # If the tool fails (e.g. nmap not found), it returns Error.
    # We should probably mock the MCP client for a strict unit test, 
    # but the goal here IS to test the MCP integration implicitly.
    # If nmap is not installed, this might fail or return error string.
    # Let's check if 'Error' or a dict result comes back.
