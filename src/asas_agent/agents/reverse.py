from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph

def create_reverse_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Reverse Agent.
    """
    system_prompt = (
        "你是 CTF-ASAS 逆向工程专家 (ReverseAgent)。\n"
        "你的主要职责：\n"
        "1. 使用 `reverse_ghidra_decompile` 分析二进制程序。\n"
        "2. 提取核心算法逻辑（加密、校验、逻辑跳转）。\n"
        "3. 编写 Python 或 C 代码辅助模拟程序行为。\n"
        "4. 找到并解密 Hardcoded 的 Flag 或生成输入序列。"
    )
    
    graph = create_react_agent_graph(llm, tools)
    return graph
