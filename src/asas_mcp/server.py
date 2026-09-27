from mcp.server.fastmcp import FastMCP, Image
from . import __version__
from .tools import recon, crypto, misc, reverse, platform, reverse_ghidra, web, kali, sandbox, vms_vnc
import base64
import os
import base64

# 创建 MCP Server 实例
#
# log_level 必须在这里显式传，不能指望 FASTMCP_LOG_LEVEL 环境变量自己生效：
# FastMCP.__init__ 的形参默认值是 "INFO"，它会作为**显式值**写进 Settings，
# 而显式值优先级高于 env（已实测：设了 FASTMCP_LOG_LEVEL=ERROR，settings 仍是 INFO）。
# 结果是每次工具调用都往 stderr 打一行 "Processing request of type ..."，
# 而这行的发出方是子进程，父进程怎么调级别都压不住。
# 这里读同一个环境变量：父进程 asas_agent CLI 按 --debug 下发，默认 WARNING 保持输出干净。
_LOG_LEVEL = os.environ.get("FASTMCP_LOG_LEVEL", "WARNING").upper()
if _LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    # 环境变量写错不该让整个工具服务器起不来，退回默认值即可
    _LOG_LEVEL = "WARNING"

mcp_server = FastMCP("asas-core-mcp", log_level=_LOG_LEVEL)

@mcp_server.tool()
async def open_vm_vnc(vm_name: str) -> str:
    """Opens a Browser-based VNC (NoVNC) session for the specified virtual machine (e.g., 'kali', 'pentest-windows') to enable direct remote interaction."""
    return await vms_vnc.open_vm_vnc(vm_name)

@mcp_server.tool()
async def vnc_capture_screen(vm_name: str, output_path: str = "/tmp/vnc_screenshot.png") -> Image:
    """[VNC GUI] Takes a screenshot of the specified VM's VNC screen.
    The tool returns the raw Image object, visible to Vision-capable LLMs.
    """
    res = await vms_vnc.vnc_capture_screen(vm_name, output_path)
    if "Error" in res or not os.path.exists(output_path):
        raise ValueError(f"Failed to capture screen: {res}")
        
    with open(output_path, "rb") as f:
        data = f.read()
    return Image(data=data, format="png")

@mcp_server.tool()
async def vnc_mouse_click(vm_name: str, x: int, y: int, button: int = 1, double: bool = False) -> str:
    """[VNC GUI] Moves the mouse to absolute coordinates (x, y) and performs a click on the specified VM."""
    return await vms_vnc.vnc_mouse_click(vm_name, x, y, button, double)

@mcp_server.tool()
async def vnc_keyboard_type(vm_name: str, text: str, append_enter: bool = False) -> str:
    """[VNC GUI] Types the specified literal text on the specified VM."""
    return await vms_vnc.vnc_keyboard_type(vm_name, text, append_enter)

@mcp_server.tool()
async def vnc_send_key(vm_name: str, key: str) -> str:
    """[VNC GUI] Sends a special key (e.g. enter, esc, ctrl-c, f1, etc.) on the VM."""
    return await vms_vnc.vnc_send_key(vm_name, key)

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
def misc_run_python(code: str) -> str:
    """[安全沙箱] 在隔离容器内运行 Python 代码
    
    Args:
        code: 完整的 Python 代码
    """
    return sandbox.run_python(code)

@mcp_server.tool()
def sandbox_execute(code: str, language: str = "python") -> str:
    """[安全沙箱] 在隔离容器内运行多种语言代码 (python/bash)
    
    Args:
        code: 脚本代码
        language: 语言类型 (python/bash)
    """
    return sandbox.run_in_sandbox(code, language)

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

@mcp_server.tool()
def reverse_ghidra_decompile(file_path: str) -> dict:
    """[逆向] 使用 Ghidra 反编译二进制文件的所有用户函数，返回每个函数的名称、地址和 C 伪代码。
    
    Args:
        file_path: 宿主机上的二进制文件绝对路径
        
    Returns:
        包含所有用户函数及其反编译 C 代码的字典
    """
    return reverse_ghidra.analyze_binary(file_path)

@mcp_server.tool()
def ghidra_list_functions(file_path: str) -> dict:
    """[逆向-轻量] 快速列出二进制文件中的所有用户函数名称和地址（不反编译，速度快）。
    适合首次侦察时使用，确定关键函数后再调用 ghidra_decompile_function 深入分析。
    
    Args:
        file_path: 宿主机上的二进制文件绝对路径
    """
    return reverse_ghidra.list_functions(file_path)

@mcp_server.tool()
def ghidra_decompile_function(file_path: str, function_name: str) -> dict:
    """[逆向-精准] 反编译二进制文件中指定名称的单个函数，返回其 C 伪代码。
    需要先用 ghidra_list_functions 获取函数列表，再对目标函数调用此工具。
    
    Args:
        file_path: 宿主机上的二进制文件绝对路径
        function_name: 要反编译的目标函数名称（如 main, check_flag）
    """
    return reverse_ghidra.decompile_function(file_path, function_name)

# --- Web Pentest Tools ---

@mcp_server.tool()
def web_dir_scan(url: str, custom_words: list = None) -> dict:
    """[Web] 扫描目标 URL 的公共目录与文件
    
    Args:
        url: 目标基础 URL (例如 http://example.com)
        custom_words: 自定义字典 (可选)
    """
    return web.dir_scan(url, custom_words)

@mcp_server.tool()
def web_sql_check(url: str, param: str) -> dict:
    """[Web] 对指定参数执行基础 SQL 注入检测
    
    Args:
        url: 目标 URL
        param: 要测试的参数名
    """
    return web.sql_check(url, param)

@mcp_server.tool()
def web_extract_links(url: str) -> dict:
    """[Web] 提取页面内的所有链接与表单结构
    
    Args:
        url: 要爬取的 URL
    """
    return web.extract_links(url)

# --- Platform Integration ---

@mcp_server.tool()
def platform_get_challenge(url: str, token: str = None) -> str:
    """从 CTF 平台获取题目详情
    
    Args:
        url: 题目详情页 URL 或 API URL
        token: 平台 API Token (可选)
        
    Returns:
        题目详情字符串 (包含描述、分类等)
    """
    return platform.platform_get_challenge(url, token)

@mcp_server.tool()
def platform_submit_flag(base_url: str, challenge_id: str, flag: str, token: str = None) -> str:
    """向 CTF 平台提交 Flag
    
    Args:
        base_url: 平台基础 URL (例如 https://ctf.example.com)
        challenge_id: 题目 ID
        flag: 解出的 Flag 字符串
        token: 平台 API Token (可选)
        
    Returns:
        提交结果及平台反馈
    """
    return platform.platform_submit_flag(challenge_id, flag, base_url, token)


# --- Kali VM Integration ---

@mcp_server.tool()
def kali_sqlmap(url: str, args: str = "--batch --banner") -> str:
    """[Kali] 使用 sqlmap 执行自动化 SQL 注入检测与利用"""
    return kali.sqlmap(url, args)

@mcp_server.tool()
def kali_upload_file(host_path: str, guest_path: str = "/tmp/") -> str:
    """[Kali] 将本地物理机(宿主机)的文件上传到 Kali 虚拟机中，返回虚拟机内的路径以供后续分析使用"""
    return kali.upload_file(host_path, guest_path)

@mcp_server.tool()
def kali_file(file_path_guest: str) -> str:
    """[Kali] 使用 file 命令判断文件架构 (ELF32/64, Strip等)"""
    return kali.file_cmd(file_path_guest)

@mcp_server.tool()
def kali_checksec(file_path_guest: str) -> str:
    """[Kali] 使用 checksec 工具检查二进制文件的安全选项保护 (NX, PIE, Canary等)"""
    return kali.checksec(file_path_guest)

@mcp_server.tool()
def kali_dirsearch(url: str, args: str = "-e php,html,js") -> str:
    """[Kali] 使用 dirsearch 执行 Web 路径爆破"""
    return kali.dirsearch(url, args)

@mcp_server.tool()
def kali_nmap(target: str, args: str = "-F") -> str:
    """[Kali] 使用 nmap 执行专业级端口扫描与指纹识别"""
    return kali.nmap(target, args)

@mcp_server.tool()
def kali_steghide(file_path: str, passphrase: str = "") -> str:
    """[Kali] 使用 steghide 提取隐藏信息"""
    return kali.steghide(file_path, passphrase)

@mcp_server.tool()
def kali_zsteg(file_path: str) -> str:
    """[Kali] 使用 zsteg 进行图片 LSB 隐写检测"""
    return kali.zsteg(file_path)

@mcp_server.tool()
def kali_binwalk(file_path: str, extract: bool = True) -> str:
    """[Kali] 使用 binwalk 分析并提取文件"""
    return kali.binwalk(file_path, extract)

@mcp_server.tool()
def kali_foremost(file_path: str) -> str:
    """[Kali] 使用 foremost 恢复文件"""
    return kali.foremost(file_path)

@mcp_server.tool()
def kali_tshark(file_path: str, filter: str = "") -> str:
    """[Kali] 使用 tshark 分析流量包 (pcap)"""
    return kali.tshark(file_path, filter)

@mcp_server.tool()
def kali_exec(cmd_str: str) -> str:
    """[Kali] 在 Kali 虚拟机内执行任意 shell 命令"""
    return kali.get_executor().execute(cmd_str)

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

# --- WP Search & Script Registry Integration ---
from .memory.wp_search import WPSearchEngine
from .memory.script_registry import ScriptRegistry

_wp_engine = None
_script_registry = None

def _get_wp_engine() -> WPSearchEngine:
    global _wp_engine
    if _wp_engine is None:
        _wp_engine = WPSearchEngine("data/writeups/wp_index.db")
    return _wp_engine

def _get_script_registry() -> ScriptRegistry:
    global _script_registry
    if _script_registry is None:
        _script_registry = ScriptRegistry("data/scripts/ctf_tools")
    return _script_registry

@mcp_server.tool()
def search_writeups(
    query: str = "",
    competition: str = None,
    category: str = None,
    year: int = None,
    limit: int = 10
) -> list:
    """在 1156 篇历年 CTF 大赛 WriteUp 中搜索解题思路。

    Args:
        query: 搜索关键词（如 "SQL注入 WAF绕过"、"RSA共模攻击"）
        competition: 过滤赛事名（如 "强网杯"、"HITCON"、"西湖论剑"）
        category: 过滤方向（web / crypto / pwn / reverse / misc）
        year: 过滤年份（如 2024）
        limit: 返回结果数量上限

    Returns:
        匹配的 WriteUp 列表，每个包含 title/competition/category/year/snippet
    """
    engine = _get_wp_engine()
    return engine.search(query=query, competition=competition, category=category, year=year, limit=limit)

@mcp_server.tool()
def list_ctf_scripts(category: str = None) -> list:
    """列出可用的 CTF 解题脚本工具。

    Args:
        category: 过滤分类（crypto / stego / traffic / web / misc / reverse）。不传则返回全部。

    Returns:
        脚本列表，每个包含 name/category/path/script_count
    """
    registry = _get_script_registry()
    return registry.list_scripts(category=category)

@mcp_server.tool()
def run_ctf_script(script_keyword: str, args: str = "") -> str:
    """查找并在 Docker 沙箱中执行 CTF 解题脚本。

    Args:
        script_keyword: 脚本关键词（如 "RSA"、"CRC32"、"USB流量"）
        args: 传给脚本的命令行参数

    Returns:
        脚本执行输出
    """
    registry = _get_script_registry()
    script = registry.find_script(script_keyword)
    if not script:
        available = [s['name'] for s in registry.list_scripts()]
        return f"未找到匹配 '{script_keyword}' 的脚本。可用脚本: {available}"

    cmd = f"python3 {script['path']}"
    if args:
        cmd += f" {args}"

    return sandbox.execute_in_sandbox(cmd)

# 保留 FastAPI 兼容性
def create_app():
    """创建 FastAPI 应用（用于 HTTP 访问）"""
    from fastapi import FastAPI
    app = FastAPI(title="ASAS Core MCP")
    
    @app.get("/")
    def root():
        # 原先硬编码 "0.1.0"，与发布版本无关；改为读包内版本，
        # 唯一权威见仓库根 pyproject.toml。
        return {"message": "ASAS Core MCP Server", "version": __version__}
    
    @app.get("/tools")
    def list_tools():
        return {
            "tools": [
                "recon_scan",
                "crypto_decode",
                "misc_identify_file",
                "misc_run_python",
                "sandbox_execute",
                "reverse_extract_strings",
                "reverse_ghidra_decompile",
                "web_dir_scan",
                "web_sql_check",
                "web_extract_links",
                "kali_sqlmap",
                "kali_upload_file",
                "kali_file",
                "kali_checksec",
                "kali_dirsearch",
                "kali_nmap",
                "kali_steghide",
                "kali_zsteg",
                "kali_tshark",
                "kali_binwalk",
                "kali_foremost",
                "kali_exec",
                "platform_get_challenge",
                "platform_submit_flag",
                "vnc_capture_screen",
                "vnc_mouse_click",
                "vnc_keyboard_type",
                "vnc_send_key",
                "search_writeups",
                "list_ctf_scripts",
                "run_ctf_script"
            ]
        }
    
    return app
