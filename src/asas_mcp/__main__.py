import asyncio
from mcp.server.stdio import stdio_server
from .server import mcp_server

async def main():
    """MCP Server 主入口 - 基于 Stdio"""
    # FastMCP handles stdio server setup internally
    await mcp_server.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
