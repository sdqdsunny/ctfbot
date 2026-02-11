from langchain_core.tools import tool
from typing import List, Optional, Dict, Any
from asas_mcp.tools import crypto, web, kali, recon, misc, sandbox, platform, reverse_ghidra

# Crypto Tools
@tool
def crypto_decode_tool(content: str, method: str = "auto") -> str:
    """解码常见编码格式 (base64/hex/url/rot13/caesar/morse/auto)"""
    return crypto.decode(content, method)

# Web Tools
@tool
def web_dir_scan_tool(url: str, custom_words: List[str] = None) -> Dict[str, Any]:
    """扫描目标 URL 的公共目录与文件"""
    return web.dir_scan(url, custom_words)

@tool
def web_sql_check_tool(url: str, param: str) -> Dict[str, Any]:
    """对指定参数执行基础 SQL 注入检测"""
    return web.sql_check(url, param)

@tool
def web_extract_links_tool(url: str) -> Dict[str, Any]:
    """提取页面内的所有链接与表单结构"""
    return web.extract_links(url)

# Kali Tools
@tool
async def kali_sqlmap_tool(url: str, args: str = "--batch --banner") -> str:
    """使用 sqlmap 执行自动化 SQL 注入检测与利用"""
    return kali.sqlmap(url, args)

@tool
async def kali_dirsearch_tool(url: str, args: str = "-e php,html,js") -> str:
    """使用 dirsearch 执行 Web 路径爆破"""
    return kali.dirsearch(url, args)

@tool
async def kali_nmap_tool(target: str, args: str = "-F") -> str:
    """使用 nmap 执行专业级端口扫描与指纹识别"""
    return kali.nmap(target, args)

# Recon Tools
@tool
def recon_scan_tool(target: str, ports: str = "1-1000") -> Dict[str, Any]:
    """执行网络侦察扫描"""
    return recon.scan(target, ports)

# Misc/Sandbox Tools
@tool
def misc_run_python_tool(code: str) -> str:
    """在安全沙箱容器内运行 Python 代码"""
    return sandbox.run_python(code)

@tool
def sandbox_execute_tool(code: str, language: str = "python") -> str:
    """在隔离容器内运行多种语言代码 (python/bash)"""
    return sandbox.run_in_sandbox(code, language)

# Platform Tools
@tool
def platform_get_challenge_tool(url: str, token: str = None) -> str:
    """从 CTF 平台获取题目详情"""
    return platform.platform_get_challenge(url, token)

@tool
def platform_submit_flag_tool(challenge_id: str, flag: str, base_url: str, token: str = None) -> str:
    """向 CTF 平台提交 Flag"""
    return platform.platform_submit_flag(challenge_id, flag, base_url, token)

# Tool Whitellist for Agent Types
TOOL_WHITELIST = {
    "crypto": [crypto_decode_tool, misc_run_python_tool, sandbox_execute_tool],
    "web": [web_dir_scan_tool, web_sql_check_tool, web_extract_links_tool, kali_sqlmap_tool, kali_dirsearch_tool],
    "reverse": [reverse_ghidra.analyze_binary, misc_run_python_tool, sandbox_execute_tool],
    "recon": [recon_scan_tool, kali_nmap_tool],
    "writeup": [], # Writeup agent usually doesn't need external tools, just its state
    "memory": [] # Memory tools are often handled separately or via retrieval
}

def get_tools_for_agent(agent_type: str) -> List[Any]:
    """Get the filtered list of tools for a specific agent type."""
    return TOOL_WHITELIST.get(agent_type, [])
