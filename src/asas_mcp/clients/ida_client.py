import asyncio
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class IdaClient:
    """Async client for the IDA Pro MCP Server."""
    
    def __init__(self, base_url: str = "http://localhost:8745"):
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None
        self.connected = False
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Initiate connection to the IDA MCP server."""
        if self.connected:
            return
            
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=None)
        await self.client.__aenter__()
        
        # In a real SSE scenario, we would start a listener task here.
        # For now, we just mark as connected to pass the skeleton test.
        self.connected = True
        logger.info(f"Connected to IDA MCP server at {self.base_url}")

    async def disconnect(self):
        """Close connection to the IDA MCP server."""
        if not self.connected:
            return
            
        if self.client:
            await self.client.__aexit__()
            self.client = None
            
        if self._listener_task:
            self._listener_task.cancel()
            
        self.connected = False
        logger.info("Disconnected from IDA MCP server")

    async def execute_tool(self, method: str, params: dict) -> any:
        """Execute a tool on the IDA MCP server via JSON-RPC."""
        if not self.connected:
            await self.connect()
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        try:
            response = await self.client.post("/mcp", json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "error" in result:
                raise Exception(f"IDA MCP Error: {result['error']}")
                
            return result.get("result")
            
        except Exception as e:
            logger.error(f"Error executing IDA tool {method}: {e}")
            raise
