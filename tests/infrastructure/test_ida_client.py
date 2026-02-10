import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from asas_mcp.clients.ida_client import IdaClient


@pytest.mark.asyncio
async def test_ida_client_connect():
    """Test that IdaClient can initiate SSE connection."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        # Create client and connect
        client = IdaClient(base_url="http://localhost:8745")
        await client.connect()
        
        # Verify connection was attempted
        mock_client_class.assert_called_once()
        assert client.connected is True


@pytest.mark.asyncio
async def test_ida_client_disconnect():
    """Test that IdaClient can disconnect properly."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        client = IdaClient(base_url="http://localhost:8745")
        await client.connect()
        await client.disconnect()
        
        assert client.connected is False


@pytest.mark.asyncio
async def test_ida_client_execute_tool():
    """Test that IdaClient can execute a tool via JSON-RPC."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client
        
        # Mock successful JSON-RPC response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": "void main() { ... }",
            "id": 1
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        
        client = IdaClient(base_url="http://localhost:8745")
        await client.connect()
        
        result = await client.execute_tool("decompile", {"addr": "0x401000"})
        
        # Verify POST was called correctly
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["method"] == "decompile"
        assert call_kwargs["json"]["params"]["addr"] == "0x401000"
        assert result == "void main() { ... }"
