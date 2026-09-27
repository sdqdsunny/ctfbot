from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph
from langchain_core.messages import SystemMessage

def create_crypto_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Crypto Agent.
    """
    system_prompt = (
        "你是 CTF-ASAS 密码学专家 (CryptoAgent)。\n"
        "你的主要职责：\n"
        "1. 识别并破解各种编码（Base64, Hex, URL 等）。\n"
        "2. 识别并解密经典密码（凯撒、维吉尼亚、栅栏等）。\n"
        "3. 进行简单的数学运算与频率分析。\n"
        "4. 如果需要，可以使用 Python 脚本进行自动化计算。\n"
        "5. **事实汇报**：如果你发现了关键事实（如：确认了某种加密算法、提取了部分明文、发现了可能的密钥），"
        "请在回答的最后一行按此格式输出：FACTS: { \"crypto_found\": \"...\" }\n"
        "你的目标是找到并返回 Flag。"
    )
    
    # In a real implementation, we would subset the tools here.
    # For now, we use the graph factory.
    graph = create_react_agent_graph(llm, tools, system_prompt=system_prompt)
    return graph
