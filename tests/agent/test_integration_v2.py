import pytest
from asas_agent.mcp_client.client import MCPToolClient

@pytest.mark.asyncio
async def test_platform_tools_registered():
    """Test that platform tools are properly registered in MCP server"""
    client = MCPToolClient()
    
    # List all tools
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    
    # Verify platform tools are registered
    assert "platform_get_challenge" in tool_names
    assert "platform_submit_flag" in tool_names
    
    print(f"✓ Found {len(tool_names)} tools, including platform tools")


@pytest.mark.asyncio
async def test_platform_get_challenge_via_mcp():
    """Test calling platform_get_challenge through MCP client"""
    client = MCPToolClient()
    
    # Call the tool with mock URL
    result = await client.call_tool(
        "platform_get_challenge",
        {"url": "http://mock-ctf.local/challenges/123"}  # token is optional, omit it
    )
    
    # Verify result format
    assert isinstance(result, str)
    assert "题目:" in result or "Mock Challenge" in result
    
    print(f"✓ platform_get_challenge returned: {result[:100]}...")


@pytest.mark.asyncio
async def test_platform_submit_flag_via_mcp():
    """Test calling platform_submit_flag through MCP client"""
    client = MCPToolClient()
    
    # Call the tool with mock data
    result = await client.call_tool(
        "platform_submit_flag",
        {
            "base_url": "http://mock-ctf.local",
            "challenge_id": "123",
            "flag": "flag{test}"
            # token is optional, omit it
        }
    )
    
    # Verify result format
    assert isinstance(result, str)
    assert "Status:" in result or "Message:" in result
    
    print(f"✓ platform_submit_flag returned: {result}")

