from asas_mcp.server import mcp_server
import base64

def test_mcp_server_has_tools():
    """测试 MCP Server 是否正确注册了工具"""
    # FastMCP 通过装饰器注册工具
    # 我们验证工具函数是否存在
    assert hasattr(mcp_server, '_tool_manager')
    
    # 获取已注册的工具
    tools = list(mcp_server._tool_manager._tools.keys())
    
    # 验证核心工具已注册
    assert "recon_scan" in tools
    assert "crypto_decode" in tools
    assert "misc_identify_file" in tools
    assert "reverse_extract_strings" in tools

def test_recon_scan_tool():
    """测试 recon_scan 工具"""
    from asas_mcp.server import recon_scan
    result = recon_scan(target="127.0.0.1", ports="80")
    assert result["target"] == "127.0.0.1"
    assert "scan_result" in result

def test_crypto_decode_tool():
    """测试 crypto_decode 工具"""
    from asas_mcp.server import crypto_decode
    result = crypto_decode(content="SGVsbG8gV29ybGQ=", method="base64")
    assert result == "Hello World"

def test_misc_identify_file_tool():
    """测试 misc_identify_file 工具"""
    from asas_mcp.server import misc_identify_file
    # PNG 文件头的 Base64 编码
    png_header = base64.b64encode(b'\x89PNG\r\n\x1a\n').decode()
    result = misc_identify_file(data_base64=png_header)
    assert result["type"] == "PNG"

def test_reverse_extract_strings_tool():
    """测试 reverse_extract_strings 工具"""
    from asas_mcp.server import reverse_extract_strings
    # 二进制数据的 Base64 编码
    binary_data = base64.b64encode(b'Hello\x00\x00World\x00Test\x00').decode()
    result = reverse_extract_strings(data_base64=binary_data, min_length=4)
    assert "Hello" in result
    assert "World" in result
