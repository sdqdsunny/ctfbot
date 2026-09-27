import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os

# This test requires the mcp server to be runnable as a script or module
# We can use "poetry run mcp-server-asas" if installed, or "python -m src.asas_mcp"
# Assuming "src" is in python path, we can run "python3 -m asas_mcp" if __main__.py exists?
# server.py defines mcp_server. 
# We need to ensure we can run it.
# Let's use the same command as dev usage if possible.

SERVER_SCRIPT_PATH = "src/asas_mcp/server.py" 
# or use module syntax if configured

@pytest.mark.asyncio
async def test_agent_memory_e2e():
    """
    End-to-End test for Memory Layer.
    Starts the MCP server process and connects to it using an MCP Client.
    """
    
    # We will invoke the server using python -m mcp run src/asas_mcp/server.py
    # But FastMCP runs via 'mcp run path/to/file.py' usually? 
    # Or plain python execution if using mcp_server.run()
    
    # Let's try to run it as a module if possible, or just point to server.py
    # Ideally we should mimic how the agent will call it.
    
    # For now, let's assume we can run it via `fastmcp run src/asas_mcp/server.py`
    # Warning: `fastmcp` might not be in path easily in test environment.
    
    # Alternative: Create a simple entrypoint script that calls mcp_server.run("stdio")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + "/src:" + env.get("PYTHONPATH", "")
    
    # Construct command to run server
    # We can use `python -m asas_mcp` if we had a __main__, but we don't yet.
    # Let's create a temporary entrypoint for the test? 
    # Or invoke python -c "from asas_mcp.server import mcp_server; mcp_server.run('stdio')"
    
    server_params = StdioServerParameters(
        command="poetry",
        args=["run", "python", "-c", "from asas_mcp.server import mcp_server; mcp_server.run('stdio')"],
        env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify tools exist
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            assert "memory_add" in tool_names
            assert "memory_query" in tool_names
            
            # Add Knowledge
            add_result = await session.call_tool(
                "memory_add",
                arguments={
                    "content": "E2E Test Knowledge: The capital of Mars is Elonville.",
                    "metadata": {"source": "e2e_test"},
                    "doc_id": "e2e_1"
                }
            )
            # Result is likely TextContent list
            # We don't strictly check return value here, just that it didn't error
            
            # Query Knowledge
            query_result = await session.call_tool(
                "memory_query",
                arguments={
                    "query": "capital of Mars",
                    "n_results": 1
                }
            )
            
            # Check content
            # query_result.content is a list of TextContent/ImageContent
            # We expect TextContent with JSON string
            
            assert len(query_result.content) > 0
            if hasattr(query_result.content[0], 'text'):
                import json
                text = query_result.content[0].text
                data = json.loads(text)
                
                # Check data
                if isinstance(data, list):
                    assert len(data) > 0
                    assert "Elonville" in data[0]['content']
                elif isinstance(data, dict):
                    assert "Elonville" in data.get('content', '')
