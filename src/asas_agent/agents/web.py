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
        "1. 使用 `kali_dirsearch_tool` 进行目录爆破。\n"
        "2. 使用 `kali_sqlmap_tool` 执行 SQL 注入检测。你必须使用任务中提供的具体 URL 进行测试。\n"
        "3. 通常先获取 --banner，然后 --dbs，然后 -D db_name --tables，最后 --dump。\n"
        "4. **格式要求**：如果参数需要引号，请确保转义。例如：CALL: kali_sqlmap_tool(url=\"http://target.com/page.php?id=1\", args=\"--batch --banner\")\n"
        "5. 分析 Web 页面内容，寻找隐藏的 Flag 或逻辑漏洞。\n\n"
        "注意：严禁使用 'http://...' 或 'target.url' 等占位符，必须替换为真实的测试目标。"
    )
    
    graph = create_react_agent_graph(llm, tools, system_prompt=system_prompt)
    return graph
