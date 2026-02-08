from typing import List, Dict
from .base import LLMProvider

class MockLLM(LLMProvider):
    """Mock LLM for development and testing."""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        if not messages:
            return "unknown"
            
        user_msg = messages[-1]["content"].lower()

        if "platform_fetch" in user_msg or (user_msg.startswith("http") and "scan" not in user_msg and "扫描" not in user_msg):
            return "platform_fetch"
            
        if "sql 注入已确认" in user_msg.lower():
            return "final_answer" 

        # Context-aware rules
        if "Explore found path" in user_msg or "login.php" in user_msg:
            if "sqli" in user_msg or "注入" in user_msg or "sqlmap" in user_msg:
                return "kali_sqlmap"
            return "kali_sqlmap" 

        # Simple rule-based matching
        if "base64" in user_msg or "解码" in user_msg or "decode" in user_msg or "morse" in user_msg or "摩斯" in user_msg or "caesar" in user_msg or "凯撒" in user_msg:
            return "crypto_decode"
        elif "扫描" in user_msg or "scan" in user_msg:
            if "http" in user_msg or "目录" in user_msg:
                return "kali_dirsearch"
            return "recon_scan"
        elif "nmap" in user_msg or "扫描端口" in user_msg:
            return "kali_nmap"
        elif "隐写" in user_msg or "steghide" in user_msg:
            return "kali_steghide"
        elif "zsteg" in user_msg:
            return "kali_zsteg"
        elif "流量" in user_msg or "tshark" in user_msg or "pcap" in user_msg:
            return "kali_tshark"
        elif "binwalk" in user_msg:
            return "kali_binwalk"
        elif "foremost" in user_msg:
            return "kali_foremost"
        elif "文件" in user_msg or "file" in user_msg:
            return "misc_identify_file"
        elif "分析" in user_msg and "代码" in user_msg:
            # Simulate analyzing C code and generating a Python solver
            return "generate_solver"
        elif "kali" in user_msg:
            return "kali_exec"
        elif "decompile" in user_msg or "反编译" in user_msg:
            return "reverse_ghidra_decompile"
        elif "目录" in user_msg or "dir" in user_msg:
            return "kali_dirsearch"
        elif "注入" in user_msg or "sqli" in user_msg:
            return "kali_sqlmap"
        elif "沙箱" in user_msg or "sandbox" in user_msg or "运行" in user_msg and "脚本" in user_msg:
            return "sandbox_execute"
        elif "爬取" in user_msg or "links" in user_msg:
            return "web_extract_links"
        
        return "unknown"
