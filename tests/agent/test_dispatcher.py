import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from asas_agent.graph.workflow import create_orchestrator_graph
from asas_agent.graph.dispatcher import dispatch_to_agent
from asas_agent.llm.mock_react import ReActMockLLM

@pytest.mark.asyncio
async def test_orchestrator_dispatch_flow():
    # Use a mock LLM that will call the dispatch_to_agent tool
    mock_llm = ReActMockLLM()
    # Mock behavior: For 'solve challenge 1', call 'dispatch_to_agent'
    
    tools = [dispatch_to_agent]
    app = create_orchestrator_graph(mock_llm, tools)
    
    # Mock the LLM's invoke to return a tool call
    with patch.object(mock_llm, "invoke") as mock_invoke:
        mock_invoke.side_effect = [
            AIMessage(content="", tool_calls=[{
                "name": "dispatch_to_agent",
                "args": {
                    "agent_type": "crypto",
                    "task": "Decode this: SGVsbG8=",
                    "platform_context": {"challenge_id": "1"}
                },
                "id": "call_1",
                "type": "tool_call"
            }]),
            AIMessage(content="Challenge 1 solved successfully!")
        ]
        
        state = {
            "messages": [HumanMessage(content="Solve challenge 1")],
            "platform_url": "http://test.com",
            "platform_token": "token"
        }
        
        result = await app.ainvoke(state)
        
        # Verify orchestrator node called LLM
        assert mock_invoke.call_count == 2
        # Verify last message is the final answer
        assert "solved successfully" in str(result["messages"][-1].content)
        # Verify tool message is in the history
        assert any(isinstance(m, ToolMessage) and m.name == "dispatch_to_agent" for m in result["messages"])

def test_agent_result_schema():
    from asas_agent.graph.dispatcher import AgentResult
    res = AgentResult(status="success", flag="flag{test}", reasoning="Applied base64 decoding")
    assert res.status == "success"
    assert res.flag == "flag{test}"
    assert "Applied" in res.reasoning
