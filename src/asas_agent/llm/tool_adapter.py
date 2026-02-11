from langchain_core.tools import StructuredTool
from ..mcp_client.client import MCPToolClient
from typing import List, Any
import asyncio

async def convert_mcp_to_langchain_tools(mcp_client: MCPToolClient) -> List[StructuredTool]:
    """Convert MCP tools to LangChain StructuredTool format"""
    mcp_tools = await mcp_client.list_tools()
    langchain_tools = []
    
    from pydantic import create_model, Field
    
    for tool in mcp_tools:
        print(f"DEBUG: Processing tool schema for {tool.name}")
        # Create closure to capture tool name
        def make_wrapper(tool_name: str):
            async def _wrapper(**kwargs):
                # 预处理参数：规避 Pydantic 或 LangChain 产生的 v__args 嵌套
                final_args = {}
                for k, v in kwargs.items():
                    if k == 'v__args' and isinstance(v, dict):
                        final_args.update(v)
                    else:
                        final_args[k] = v
                
                # print(f"DEBUG: _wrapper tool={tool_name} final_args={final_args}")
                return await mcp_client.call_tool(tool_name, final_args)
            _wrapper.__name__ = tool_name
            return _wrapper
        
        # DEPRECATED: Pydantic based args_schema is causing v__args conflicts with local LLMs
        # For robustness, we now use a clean wrapper without strict validation
        
        lc_tool = StructuredTool.from_function(
            coroutine=make_wrapper(tool.name),
            name=tool.name,
            description=tool.description or "No description",
            args_schema=None # Disable strict pydantic validation to avoid v__args injection
        )
        langchain_tools.append(lc_tool)
        
    return langchain_tools
