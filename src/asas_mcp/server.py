from mcp.server.fastmcp import FastMCP
from .tools import recon, crypto, misc, reverse
import base64

# 创建 MCP Server 实例
mcp_server = FastMCP("asas-core-mcp")

@mcp_server.tool()
def recon_scan(target: str, ports: str = "1-1000") -> dict:
    """执行网络侦察扫描
    
    Args:
        target: 目标 IP 地址或域名
        ports: 端口范围，默认 1-1000
        
    Returns:
        扫描结果字典
    """
    return recon.scan(target, ports)

@mcp_server.tool()
def crypto_decode(content: str, method: str = "auto") -> str:
    """解码常见编码格式
    
    Args:
        content: 待解码的内容
        method: 解码方法 (base64/hex/url/auto)
        
    Returns:
        解码后的字符串
    """
    return crypto.decode(content, method)

@mcp_server.tool()
def misc_identify_file(data_base64: str) -> dict:
    """识别文件类型
    
    Args:
        data_base64: Base64 编码的文件数据
        
    Returns:
        文件类型信息字典
    """
    data = base64.b64decode(data_base64)
    return misc.identify_file_type(data)

@mcp_server.tool()
def reverse_extract_strings(data_base64: str, min_length: int = 4) -> list:
    """从二进制数据提取字符串
    
    Args:
        data_base64: Base64 编码的二进制数据
        min_length: 最小字符串长度
        
    Returns:
        提取的字符串列表
    """
    data = base64.b64decode(data_base64)
    return reverse.extract_strings(data, min_length)

# --- Memory Layer Integration ---
from .memory.db import ChromaManager
from .memory.loader import load_initial_knowledge
import hashlib

def _get_memory_manager() -> ChromaManager:
    # Initialize on first use (singleton)
    # Also load initial knowledge if it's the first time running (empty DB)
    manager = ChromaManager()
    
    # Simple check: if collection empty, load knowledge
    # Note: This check is simplistic; loader handles duplicate checks via hash.
    # We can just call loader safely.
    load_initial_knowledge(manager)
    
    return manager

@mcp_server.tool()
def memory_add(content: str, metadata: dict = {}, doc_id: str = None) -> str:
    """Add a document to the agent's knowledge base.
    
    Args:
        content: The text content to store.
        metadata: Dictionary of metadata (e.g., source, type, timestamp).
        doc_id: Optional unique ID. If not provided, MD5 hash of content is used.
        
    Returns:
        The document ID.
    """
    manager = _get_memory_manager()
    if not doc_id:
        doc_id = hashlib.md5(content.encode('utf-8')).hexdigest()
        
    # Ensure metadata has at least one key to avoid ChromaDB error
    if not metadata:
        metadata = {"source": "user_input"}
        
    manager.add(content=content, metadata=metadata, doc_id=doc_id)
    return doc_id

@mcp_server.tool()
def memory_query(query: str, n_results: int = 5) -> list:
    """Query the agent's knowledge base.
    
    Args:
        query: The search query text.
        n_results: Number of results to return.
        
    Returns:
        List of matching documents with content and metadata.
    """
    manager = _get_memory_manager()
    return manager.query(text=query, n_results=n_results)

# 保留 FastAPI 兼容性
def create_app():
    """创建 FastAPI 应用（用于 HTTP 访问）"""
    from fastapi import FastAPI
    app = FastAPI(title="ASAS Core MCP")
    
    @app.get("/")
    def root():
        return {"message": "ASAS Core MCP Server", "version": "0.1.0"}
    
    @app.get("/tools")
    def list_tools():
        return {
            "tools": [
                "recon_scan",
                "crypto_decode",
                "misc_identify_file",
                "reverse_extract_strings"
            ]
        }
    
    return app
