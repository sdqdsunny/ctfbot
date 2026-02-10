import pytest
from unittest.mock import AsyncMock, patch
from asas_mcp.tools.ida_tools import ida_decompile, ida_xrefs_to


@pytest.mark.asyncio
async def test_ida_decompile_tool():
    """Test the ida_decompile tool wrapper."""
    with patch("asas_mcp.tools.ida_tools.get_ida_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.execute_tool.return_value = "int main() { ... }"
        
        # Test tool invocation
        # Note: @tool wrappers change the function signature slightly for langchain, 
        # but the .invoke or .run or direct async call should work in test.
        result = await ida_decompile.ainvoke({"addr": "main"})
        
        mock_client.execute_tool.assert_called_with("decompile", {"addr": "main"})
        assert "main" in result

@pytest.mark.asyncio
async def test_ida_xrefs_tool():
    """Test the ida_xrefs_to tool wrapper."""
    with patch("asas_mcp.tools.ida_tools.get_ida_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.execute_tool.return_value = ["0x401234", "0x401567"]
        
        result = await ida_xrefs_to.ainvoke({"addr": "0x401000"})
        
        mock_client.execute_tool.assert_called_with("xrefs_to", {"addrs": ["0x401000"]})
        assert "0x401234" in str(result)
