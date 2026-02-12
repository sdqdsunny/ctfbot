from typing import Dict, List, Optional
from langchain_core.tools import tool
from ..clients.ida_client import IdaClient

# Singleton client instance
_ida_client: Optional[IdaClient] = None

def get_ida_client() -> IdaClient:
    """Get or create the singleton IDA client."""
    global _ida_client
    if _ida_client is None:
        _ida_client = IdaClient()
    return _ida_client

@tool
async def ida_decompile(addr: str) -> str:
    """
    Decompile the function at the given address/name in IDA Pro.
    
    Args:
        addr: Address or function name to decompile.
        
    Returns:
        The decompiled C code as a string.
    """
    client = get_ida_client()
    try:
        result = await client.execute_tool("decompile", {"addr": addr})
        return str(result)
    except Exception as e:
        return f"Error decompiling at {addr}: {e}"

@tool
async def ida_xrefs_to(addr: str) -> str:
    """
    Get cross-references to the given address in IDA Pro.
    
    Args:
        addr: Target address to find references to.
        
    Returns:
        A string listing cross-references.
    """
    client = get_ida_client()
    try:
        result = await client.execute_tool("xrefs_to", {"addrs": [addr]})
        return str(result)
    except Exception as e:
        return f"Error fetching xrefs for {addr}: {e}"

@tool
async def ida_py_eval(code: str) -> str:
    """
    Execute arbitrary Python code within the IDA Pro context.
    
    Args:
        code: The Python code to execute.
        
    Returns:
        The result or stdout of the execution.
    """
    client = get_ida_client()
    try:
        result = await client.execute_tool("py_eval", {"code": code})
        return str(result)
    except Exception as e:
        return f"Error executing Python script: {e}"
@tool
async def ida_list_funcs() -> str:
    """
    List all functions discovered in the binary by IDA Pro.
    
    Returns:
        A list of function names and addresses.
    """
    client = get_ida_client()
    try:
        result = await client.execute_tool("list_funcs", {})
        return str(result)
    except Exception as e:
        return f"Error listing functions: {e}"

@tool
async def ida_get_imports() -> str:
    """
    Get the import table of the binary.
    
    Returns:
        A list of imported modules and functions.
    """
    client = get_ida_client()
    try:
        result = await client.execute_tool("get_imports", {})
        return str(result)
    except Exception as e:
        return f"Error fetching imports: {e}"

@tool
async def ida_find_regex(pattern: str) -> str:
    """
    Search for strings or byte patterns in the binary using regex.
    
    Args:
        pattern: The regex pattern to search for.
        
    Returns:
        A list of matches with their addresses.
    """
    client = get_ida_client()
    try:
        result = await client.execute_tool("find_regex", {"pattern": pattern})
        return str(result)
    except Exception as e:
        return f"Error searching for regex '{pattern}': {e}"
