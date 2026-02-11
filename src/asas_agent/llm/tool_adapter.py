from langchain_core.tools import StructuredTool
from ..mcp_client.client import MCPToolClient
from typing import List, Any
import asyncio

async def convert_mcp_to_langchain_tools(mcp_client: MCPToolClient) -> List[StructuredTool]:
    """Convert MCP tools to LangChain StructuredTool format"""
    mcp_tools = await mcp_client.list_tools()
    langchain_tools = []
    
    from langchain_core.tools import BaseTool
    from pydantic import Field
    
    class MCPTool(BaseTool):
        name: str = ""
        description: str = ""
        mcp_client: Any = None
        
        def _run(self, **kwargs):
            raise NotImplementedError("Use _arun")
            
        async def _arun(self, **kwargs):
            # 兼容性处理：如果所有参数被包裹在第一个 args 中
            final_args = kwargs
            if not kwargs and hasattr(self, '_args') and self._args:
                # 这种情况很少见，但以防万一
                pass
                
            print(f"DEBUG [MCPTool]: {self.name} final_args={final_args}")
            return await self.mcp_client.call_tool(self.name, final_args)

    for tool in mcp_tools:
        print(f"DEBUG: Processing tool schema for {tool.name}")
        
        lc_tool = MCPTool(
            name=tool.name,
            description=tool.description or "No description",
            mcp_client=mcp_client
        )
        langchain_tools.append(lc_tool)
        
    return langchain_tools
