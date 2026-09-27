from typing import List, Dict
from .base import LLMProvider

class MockLLM(LLMProvider):
    """Mock LLM for development and testing."""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        if not messages:
            return "unknown"
            
        # Only look at the actual task input (first line) to avoid
        # matching against the option list in the prompt.
        full_msg = messages[-1]["content"]
        # Extract first line (task description) for intent matching
        task_line = full_msg.split('\n')[0].lower() if full_msg else ""
        user_msg = full_msg.lower()  # full for context checks

        # 1. Specific content rules FIRST (high-priority keywords)
        if "gui" in task_line or "桌面" in task_line or "vnc" in task_line:
            return "zeroclaw_vnc"

        if "base64" in task_line or "解码" in task_line or "decode" in task_line or "morse" in task_line or "摩斯" in task_line or "caesar" in task_line or "凯撒" in task_line:
            return "crypto_decode"

        if "sql 注入已确认" in task_line:
            return "final_answer" 

        # 2. Context-aware rules (dispatcher tasks with explicit paths)
        if "Explore found path" in task_line or "login.php" in task_line:
            return "kali_sqlmap" 

        # 3. Tool-name matches in task line (very specific)
        if "steghide" in task_line:
            return "kali_steghide"
        if "zsteg" in task_line:
            return "kali_zsteg"
        if "tshark" in task_line or "pcap" in task_line:
            return "kali_tshark"
        if "binwalk" in task_line:
            return "kali_binwalk"
        if "foremost" in task_line:
            return "kali_foremost"
        if "sqlmap" in task_line or ("注入" in task_line and "探测" in task_line):
            return "kali_sqlmap"
        if "dirsearch" in task_line:
            return "kali_dirsearch"
        if "nmap" in task_line:
            return "kali_nmap"

        # 4. Platform fetch rules
        if "platform_fetch" in task_line:
            return "platform_fetch"
        if task_line.startswith("http") and "已尝试的历史操作" not in user_msg:
            if "scan" not in task_line and "扫描" not in task_line:
                return "platform_fetch"

        # 5. Category rules (broader matching)
        if "扫描" in task_line or "scan" in task_line:
            if "http" in task_line or "目录" in task_line:
                return "kali_dirsearch"
            return "recon_scan"
        elif "隐写" in task_line:
            return "kali_steghide"
        elif "流量" in task_line:
            return "kali_tshark"
        elif "注入" in task_line or "sqli" in task_line:
            return "kali_sqlmap"
        elif "目录" in task_line or "dir" in task_line:
            return "kali_dirsearch"
        elif "decompile" in task_line or "反编译" in task_line:
            return "reverse_ghidra_decompile"
        elif "分析" in task_line and "代码" in task_line:
            return "generate_solver"
        elif "文件" in task_line or "file" in task_line:
            return "misc_identify_file"
        elif "kali" in task_line:
            return "kali_exec"
        elif "沙箱" in task_line or "sandbox" in task_line:
            return "sandbox_execute"
        elif "爬取" in task_line or "links" in task_line:
            return "web_extract_links"
        
        return "unknown"
