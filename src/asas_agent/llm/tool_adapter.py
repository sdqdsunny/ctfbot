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
            # 处理多余的 kwargs 嵌套 (Langchain 新特性容忍)
            final_args = kwargs.get("kwargs", kwargs)
            if not final_args and hasattr(self, '_args') and self._args:
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
