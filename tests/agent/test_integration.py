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
    
    # Verify: recon_scan should appear in task history
    history = result.get("task_history", [])
    tools_run = [h["tool"] for h in history]
    assert "recon_scan" in tools_run
    # The graph may chain to dirsearch/sqlmap from pending tasks
    assert result.get("final_answer") is not None
