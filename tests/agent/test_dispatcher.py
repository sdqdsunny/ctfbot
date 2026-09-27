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


def test_tool_description_lists_every_registered_agent():
    """dispatch_to_agent 的 docstring 就是发给模型的工具描述。

    漏列某个 agent 类型等于告诉模型"这个类型不存在"——原 docstring 只写了
    crypto/web/reverse/recon 四个，pwn/writeup/memory 虽然已注册却没人知道，
    模型自然永远不会派发它们。这里把 docstring 与注册表钉在一起，
    以后新增 agent 忘了改描述会直接失败。
    """
    from asas_agent.graph.dispatcher import AGENT_CREATORS, dispatch_to_agent

    description = dispatch_to_agent.description
    assert description, "工具描述为空 —— docstring 可能被写成了非字面量（如 f-string）"

    missing = [a for a in AGENT_CREATORS if a not in description]
    assert not missing, f"工具描述里缺少已注册的 agent 类型: {missing}"
