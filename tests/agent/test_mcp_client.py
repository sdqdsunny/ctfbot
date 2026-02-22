import pytest
from unittest.mock import AsyncMock, patch
from asas_agent.mcp_client.client import MCPToolClient

@pytest.mark.asyncio
async def test_call_tool():
    # We mock the stdio_client context manager and session
    with patch("asas_agent.mcp_client.client.stdio_client") as mock_stdio:
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        # Mock result structure to match new MCP text content parsing
        mock_result = AsyncMock()
        text_item = AsyncMock()
        text_item.type = "text"
        text_item.text = "Tool Output"
        mock_result.content = [text_item]
        mock_session.call_tool.return_value = mock_result
        
        # Setup context managers
        mock_stdio.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())
        
        with patch("asas_agent.mcp_client.client.ClientSession") as MockSession:
            MockSession.return_value.__aenter__.return_value = mock_session
            
            client = MCPToolClient()
            result = await client.call_tool("test_tool", {"arg": "val"})
            
            assert result == "Tool Output"
            mock_session.call_tool.assert_called_with("test_tool", {"arg": "val"})
