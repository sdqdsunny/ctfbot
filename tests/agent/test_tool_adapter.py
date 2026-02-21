import pytest
from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_convert_mcp_tools():
    # Mock MCP Client
    mock_client = AsyncMock()
    mock_client.list_tools.return_value = [
        type("Tool", (), {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {
                "type": "object",
                "properties": {"arg1": {"type": "string"}},
                "required": ["arg1"]
            }
        })()
    ]
    
    tools = await convert_mcp_to_langchain_tools(mock_client)
    assert len(tools) == 1
    assert tools[0].name == "test_tool"
    assert tools[0].description == "A test tool"
    
    # Verify the underlying async call works correctly
    mock_client.call_tool.return_value = "Success"
    result = await tools[0].ainvoke({"arg1": "value"})
    assert result == "Success"
    mock_client.call_tool.assert_called_with("test_tool", {"arg1": "value"})

