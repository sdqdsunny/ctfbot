from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph

def create_web_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Web Agent.
    """
    system_prompt = (
        "你是 CTF-ASAS Web 渗透专家 (WebAgent)。\n"
        "你的主要职责：\n"
        "1. 使用 `kali_dirsearch` 发现路径与文件。\n"
        "2. 使用 `kali_sqlmap` 检测并利用 SQL 注入漏洞。\n"
        "3. 分析 Web 页面内容，寻找隐藏的 Flag 或逻辑漏洞。\n"
        "4. 协助进行 XSS, SSRF, RCE 等漏洞的验证。"
    )
    
    graph = create_react_agent_graph(llm, tools, system_prompt=system_prompt)
    return graph
