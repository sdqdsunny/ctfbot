from typing import List, Dict, Any
from langchain_core.tools import BaseTool, tool
from ..graph.workflow import create_react_agent_graph
from ..rag.retriever import SemanticRetriever

# Lazy load retriever
_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = SemanticRetriever()
    return _retriever

@tool
def retrieve_knowledge(query: str) -> str:
    """
    Search for similar solved problems or writeups in the knowledge base.
    Useful when stuck or looking for inspiration.
    
    Args:
        query: A description of the problem or error message.
        
    Returns:
        A string containing relevant past solutions.
    """
    try:
        retriever = get_retriever()
        docs = retriever.retrieve(query)
        if not docs:
            return "No relevant knowledge found."
        return "\n---\n".join(docs)
    except Exception as e:
        return f"Error retrieving knowledge: {e}"

def create_memory_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Memory Agent with RAG capabilities.
    """
    system_prompt = (
        "你是 CTF-ASAS 知识管理员 (MemoryAgent)。\n"
        "你的主要职责：\n"
        "1. 使用 `memory_add` 将成功的解题过程存入知识库。\n"
        "2. 使用 `retrieve_knowledge` 检索历史解题经验。\n"
        "3. 当 Orchestrator 或其他 Agent 遇到困难时，提供相关的 Writeup 片段。\n"
    )
    
    # Extend tools with retrieval capability
    enhanced_tools = tools + [retrieve_knowledge]
    
    graph = create_react_agent_graph(llm, enhanced_tools)
    return graph
