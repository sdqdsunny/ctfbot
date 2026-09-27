import pytest
from unittest.mock import AsyncMock, patch
from asas_mcp.tools.ida_tools import (
    ida_decompile, ida_xrefs_to, ida_list_funcs, ida_get_imports, ida_find_regex
)


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
@pytest.mark.asyncio
async def test_ida_list_funcs_tool():
    """Test the ida_list_funcs tool wrapper."""
    with patch("asas_mcp.tools.ida_tools.get_ida_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.execute_tool.return_value = [{"name": "main", "start": "0x401000"}]
        
        result = await ida_list_funcs.ainvoke({})
        
        mock_client.execute_tool.assert_called_with("list_funcs", {})
        assert "main" in str(result)

@pytest.mark.asyncio
async def test_ida_get_imports_tool():
    """Test the ida_get_imports tool wrapper."""
    with patch("asas_mcp.tools.ida_tools.get_ida_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.execute_tool.return_value = {"libc.so.6": ["printf", "scanf"]}
        
        result = await ida_get_imports.ainvoke({})
        
        mock_client.execute_tool.assert_called_with("get_imports", {})
        assert "printf" in str(result)

@pytest.mark.asyncio
async def test_ida_find_regex_tool():
    """Test the ida_find_regex tool wrapper."""
    with patch("asas_mcp.tools.ida_tools.get_ida_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.execute_tool.return_value = [{"addr": "0x402000", "match": "flag{test}"}]
        
        result = await ida_find_regex.ainvoke({"pattern": "flag{.*}"})
        
        mock_client.execute_tool.assert_called_with("find_regex", {"pattern": "flag{.*}"})
        assert "flag{test}" in str(result)
