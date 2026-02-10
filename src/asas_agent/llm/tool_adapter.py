from langchain_core.tools import StructuredTool
from ..mcp_client.client import MCPToolClient
from typing import List
import asyncio

async def convert_mcp_to_langchain_tools(mcp_client: MCPToolClient) -> List[StructuredTool]:
    """Convert MCP tools to LangChain StructuredTool format"""
    mcp_tools = await mcp_client.list_tools()
    langchain_tools = []
    
    for tool in mcp_tools:
        # Create closure to capture tool name
        def make_wrapper(tool_name: str):
            async def _wrapper(**kwargs):
                # LangChain passes args as kwargs, forward them to MCP
                return await mcp_client.call_tool(tool_name, kwargs)
            # Set __name__ for better debugging
            _wrapper.__name__ = tool_name
            return _wrapper
        
        lc_tool = StructuredTool.from_function(
            coroutine=make_wrapper(tool.name),
            name=tool.name,
            description=tool.description or "No description",
            # args_schema could be generated from inputSchema if needed
        )
        langchain_tools.append(lc_tool)
        
    return langchain_tools
