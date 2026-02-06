import pytest
import warnings
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
    
    # We invoke the graph
    result = await app.ainvoke(inputs)
    
    # Verify State
    assert result["task_understanding"] == "crypto_decode"
    assert result["planned_tool"] == "crypto_decode"
    assert result["tool_args"]["content"] == "SGVsbG8gV29ybGQ="
    
    # This proves we actually called the running MCP server!
    # Expected result from crypto_decode is "Hello World"
    assert "Hello World" in result["final_answer"]
    assert "Hello World" == result["tool_result"]
