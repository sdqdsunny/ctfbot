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
