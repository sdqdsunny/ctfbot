from typing import List, Dict
from .base import LLMProvider

class MockLLM(LLMProvider):
    """Mock LLM for development and testing."""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        if not messages:
            return "unknown"
            
        user_msg = messages[-1]["content"].lower()
        
        # Simple rule-based matching
        if "base64" in user_msg or "解码" in user_msg or "decode" in user_msg:
            return "crypto_decode"
        elif "扫描" in user_msg or "scan" in user_msg:
            return "recon_scan"
        elif "文件" in user_msg or "file" in user_msg:
            return "misc_identify_file"
        elif "字符串" in user_msg or "string" in user_msg:
            return "reverse_extract_strings"
        
        return "unknown"
