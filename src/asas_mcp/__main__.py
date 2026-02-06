import asyncio
from mcp.server.stdio import stdio_server
from .server import mcp_server

async def main():
    """MCP Server 主入口 - 基于 Stdio"""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
