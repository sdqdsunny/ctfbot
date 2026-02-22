from langchain_core.tools import tool
from typing import List, Optional, Dict, Any
from asas_mcp.tools import crypto, web, kali, recon, misc, sandbox, platform, reverse_ghidra

# Crypto Tools
@tool
def crypto_decode(content: str, method: str = "auto") -> str:
    """解码常见编码格式 (base64/hex/url/rot13/caesar/morse/auto)"""
    return crypto.decode(content, method)

# Web Tools
@tool
def web_dir_scan(url: str, custom_words: List[str] = None) -> Dict[str, Any]:
    """扫描目标 URL 的公共目录与文件"""
    return web.dir_scan(url, custom_words)

@tool
def web_sql_check(url: str, param: str) -> Dict[str, Any]:
    """对指定参数执行基础 SQL 注入检测"""
    return web.sql_check(url, param)

@tool
def web_extract_links(url: str) -> Dict[str, Any]:
    """提取页面内的所有链接与表单结构"""
    return web.extract_links(url)

# VNC GUI Tools (C2 Phase)
@tool
async def vnc_capture_screen(vm_name: str, output_path: str = "/tmp/vnc_screenshot.png") -> str:
    """[VNC GUI] Takes a screenshot of the specified VM's VNC screen."""
    from asas_mcp.tools import vms_vnc
    return await vms_vnc.vnc_capture_screen(vm_name, output_path)

@tool
async def vnc_mouse_click(vm_name: str, x: int, y: int, button: int = 1, double: bool = False) -> str:
    """[VNC GUI] Moves the mouse to absolute coordinates (x, y) and performs a click on the specified VM."""
    from asas_mcp.tools import vms_vnc
    return await vms_vnc.vnc_mouse_click(vm_name, x, y, button, double)

@tool
async def vnc_keyboard_type(vm_name: str, text: str, append_enter: bool = False) -> str:
    """[VNC GUI] Types the specified literal text on the specified VM."""
    from asas_mcp.tools import vms_vnc
    return await vms_vnc.vnc_keyboard_type(vm_name, text, append_enter)

@tool
async def vnc_send_key(vm_name: str, key: str) -> str:
    """[VNC GUI] Sends a special key (e.g. enter, esc, ctrl-c, f1, etc.) on the VM."""
    from asas_mcp.tools import vms_vnc
    return await vms_vnc.vnc_send_key(vm_name, key)

# Kali Tools
@tool
async def kali_sqlmap(url: str, args: str = "--batch --banner") -> str:
    """使用 sqlmap 执行自动化 SQL 注入检测与利用"""
    return kali.sqlmap(url, args)

@tool
async def kali_dirsearch(url: str, args: str = "-e php,html,js") -> str:
    """使用 dirsearch 执行 Web 路径爆破"""
    return kali.dirsearch(url, args)

@tool
async def kali_nmap(target: str = None, args: str = "-F", target_ip: str = None) -> str:
    """使用 nmap 执行专业级端口扫描与指纹识别"""
    target = target or target_ip
    if not target:
        return "Error: target or target_ip is required."
    return kali.nmap(target, args)

@tool
def kali_exec(cmd_str: str) -> str:
    """在 Kali 虚拟机内执行任意 shell 命令"""
    return kali.get_executor().execute(cmd_str)

# Recon Tools
@tool
def recon_scan(target: str, ports: str = "1-1000") -> Dict[str, Any]:
    """执行网络侦察扫描"""
    return recon.scan(target, ports)

# Misc/Sandbox Tools
@tool
def misc_run_python(code: str) -> str:
    """在安全沙箱容器内运行 Python 代码"""
    return sandbox.run_python(code)

@tool
def sandbox_execute(code: str, language: str = "python") -> str:
    """在隔离容器内运行多种语言代码 (python/bash)"""
    return sandbox.run_in_sandbox(code, language)

# Platform Tools
@tool
def platform_get_challenge(url: str, token: str = None) -> str:
    """从 CTF 平台获取题目详情"""
    return platform.platform_get_challenge(url, token)

@tool
def platform_submit_flag(challenge_id: str, flag: str, base_url: str, token: str = None) -> str:
    """向 CTF 平台提交 Flag"""
    return platform.platform_submit_flag(challenge_id, flag, base_url, token)

# Tool Whitellist for Agent Types
TOOL_WHITELIST = {
    "crypto": [crypto_decode, misc_run_python, sandbox_execute],
    "web": [
        web_dir_scan, web_sql_check, web_extract_links, 
        kali_sqlmap, kali_dirsearch, kali_exec, kali_nmap,
        vnc_capture_screen, vnc_mouse_click, vnc_keyboard_type, vnc_send_key
    ],
    "reverse": [reverse_ghidra.analyze_binary, misc_run_python, sandbox_execute],
    "recon": [recon_scan, kali_nmap, kali_exec],
    "writeup": [], # Writeup agent usually doesn't need external tools, just its state
    "memory": [] # Memory tools are often handled separately or via retrieval
}

def get_tools_for_agent(agent_type: str) -> List[Any]:
    """Get the filtered list of tools for a specific agent type."""
    return TOOL_WHITELIST.get(agent_type, [])
