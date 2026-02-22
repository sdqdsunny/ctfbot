from mcp.server.fastmcp import FastMCP
from .tools import recon, crypto, misc, reverse, platform, reverse_ghidra, web, kali, sandbox, vms_vnc, native_vnc
import base64

# 创建 MCP Server 实例
mcp_server = FastMCP("asas-core-mcp")

@mcp_server.tool()
async def open_vm_vnc(vm_name: str) -> str:
    """Opens a Browser-based VNC (NoVNC) session for the specified virtual machine (e.g., 'kali', 'pentest-windows') to enable direct remote interaction."""
    return await vms_vnc.open_vm_vnc(vm_name)

@mcp_server.tool()
async def vnc_screenshot(vm_name: str, port: int = 5900, password: str = None) -> str:
    """[VNC GUI] Takes a screenshot of the specified VM's VNC screen. Returns base64 image."""
    return await native_vnc.vnc_screenshot(vm_name, port, password)

@mcp_server.tool()
async def vnc_mouse_click(vm_name: str, x: int, y: int, button: str = "left", port: int = 5900, password: str = None) -> str:
    """[VNC GUI] Moves the mouse to (x, y) and performs a click on the specified VM."""
    return await native_vnc.vnc_mouse_click(vm_name, x, y, button, port, password)

@mcp_server.tool()
async def vnc_keyboard_type(vm_name: str, text: str, port: int = 5900, password: str = None) -> str:
    """[VNC GUI] Types the specified text on the specified VM."""
    return await native_vnc.vnc_keyboard_type(vm_name, text, port, password)


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
    """[深度分析] 使用 Ghidra 执行自动化反编译
    
    Args:
        file_path: 宿主机上的核心二进制文件绝对路径
        
    Returns:
        包含所有函数及其对应 C 伪代码的字典
    """
    return reverse_ghidra.analyze_binary(file_path)

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
                "vnc_screenshot",
                "vnc_mouse_click",
                "vnc_keyboard_type"
            ]
        }
    
    return app
