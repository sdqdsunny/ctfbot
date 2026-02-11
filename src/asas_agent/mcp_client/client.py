from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os

class MCPToolClient:
    """Client for calling MCP tools."""
    
    def __init__(self):
        # By default, connect to the local asas_mcp module
        # We need to run it as a python module
        # Assuming we are running from project root or installed package
        # We need to find the root of the project to add to PYTHONPATH for the subprocess
        # A robust way is to find where asas_mcp package is.
        # But for this MVP, we follow the plan's simple path deduction or improve it.
        # The plan suggests:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        
        self.server_params = StdioServerParameters(
            command=sys.executable, # Use current python interpreter
            args=["-m", "asas_mcp"],
            env={**os.environ, "PYTHONPATH": f"{project_root}/src"}
        )
    
    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a tool on the MCP server."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print(f"DEBUG [MCPClient]: Calling {tool_name} with {arguments}")
                result = await session.call_tool(tool_name, arguments)
                # Assuming text result for now
                if hasattr(result, 'content') and result.content:
                    return result.content[0].text
                return str(result)

    async def list_tools(self) -> list:
        """List available tools."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools
