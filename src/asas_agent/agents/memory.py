from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph

def create_memory_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Memory Agent.
    """
    system_prompt = (
        "你是 CTF-ASAS 知识管理员 (MemoryAgent)。\n"
        "你的主要职责：\n"
        "1. 使用 `memory_add` 将成功的解题过程存入知识库。\n"
        "2. 使用 `memory_query` 检索历史解题经验，为新题目提供参考策略。\n"
        "3. 管理知识库的结构，确保信息的语义准确性。\n"
        "4. 协助 Orchestrator 进行决策，避免重复劳动。"
    )
    
    graph = create_react_agent_graph(llm, tools)
    return graph
