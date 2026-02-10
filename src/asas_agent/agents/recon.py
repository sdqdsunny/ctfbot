from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph

def create_recon_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Recon Agent.
    """
    system_prompt = (
        "你是 CTF-ASAS 侦察专家 (ReconAgent)。\n"
        "你的主要职责：\n"
        "1. 对目标进行初始信息收集。\n"
        "2. 使用 `kali_nmap` 探测端口与服务。\n"
        "3. 使用 `web_extract_links` 或 `dir_scan` 发现潜在的 Web 路径。\n"
        "4. 汇报发现的攻击面，为其他专业代理提供线索。"
    )
    
    graph = create_react_agent_graph(llm, tools)
    return graph
