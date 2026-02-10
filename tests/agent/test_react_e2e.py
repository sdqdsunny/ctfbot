import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from asas_agent.graph.state import AgentState
from asas_agent.llm.mock_react import ReActMockLLM

@pytest.mark.asyncio
async def test_react_mock_e2e():
    """Test full v2 ReAct loop with Mock LLM and Mock MCP Client."""
    
    # 1. Mock MCP Client interactions
    mock_mcp_client = AsyncMock()
    
    # Define tool schema mocks
    mock_tool_def = MagicMock()
    mock_tool_def.name = "platform_get_challenge"
    mock_tool_def.description = "Fetch challenge" 
    mock_tool_def.inputSchema = {"type": "object", "properties": {"url": {"type": "string"}}}
    
    mock_tool_def_submit = MagicMock()
    mock_tool_def_submit.name = "platform_submit_flag"
    mock_tool_def_submit.description = "Submit flag"
    mock_tool_def_submit.inputSchema = {"type": "object", "properties": {"flag": {"type": "string"}}}
    
    # Mock list_tools to return our schemas
    mock_mcp_client.list_tools.return_value = [mock_tool_def, mock_tool_def_submit]
    
    # Mock call_tool to return results
    async def call_tool_side_effect(name, args):
        if name == "platform_get_challenge":
            return '{"id": "mock-1", "description": "Please submit flag{mock_flag}"}'
        if name == "platform_submit_flag":
            return '{"status": "correct", "message": "Good job!"}'
        return "Unknown tool"
        
    mock_mcp_client.call_tool.side_effect = call_tool_side_effect

    # 2. Convert tools (this logic is in tool_adapter, we test it implicitly or import usage)
    from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
    tools = await convert_mcp_to_langchain_tools(mock_mcp_client)
    assert len(tools) == 2
    
    # 3. Setup Mock LLM
    llm = ReActMockLLM()
    
    # 4. Build Graph
    from asas_agent.graph.workflow import create_react_agent_graph
    app = create_react_agent_graph(llm, tools)
    
    # 5. Execute
    inputs = {"messages": [HumanMessage(content="Start fetch http://mock/1")]}
    
    final_state = await app.ainvoke(inputs)
    messages = final_state["messages"]
    
    # 6. Verify flow
    # Expected: 
    # 0: Human "Start..."
    # 1: AI (ToolCall: platform_get_challenge)
    # 2: Tool (Result: description with flag)
    # 3: AI (ToolCall: platform_submit_flag) - MockLLM generic logic for 'flag{'
    # 4: Tool (Result: correct)
    # 5: AI "Mission accomplished..." (Final Answer)
    
    assert len(messages) >= 5
    assert isinstance(messages[1], AIMessage)
    assert messages[1].tool_calls[0]["name"] == "platform_get_challenge"
    
    assert isinstance(messages[2], ToolMessage)
    assert "flag{mock_flag}" in messages[2].content
    
    assert isinstance(messages[3], AIMessage)
    assert messages[3].tool_calls[0]["name"] == "platform_submit_flag"
    
    assert isinstance(messages[-1], AIMessage)
    assert "Mission accomplished" in messages[-1].content
