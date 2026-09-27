from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph

def create_writeup_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Writeup Agent.
    """
    system_prompt = (
        "你是 CTF-ASAS 技术文档专家 (WriteupAgent)。\n"
        "你的主要职责：\n"
        "1. 收集并分析来自各个专业代理的解题日志。\n"
        "2. 生成高质量的 Markdown 格式 Writeup。\n"
        "3. 确保报告包含：题目分析、关键步骤、所用 Payload 以及最终 Flag。\n"
        "4. 报告应简洁明了，适合技术分享。"
    )
    
    graph = create_react_agent_graph(llm, tools)
    return graph
