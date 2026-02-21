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
        "1. **爆破专家**：如果遇到登录页面，优先使用 `kali_exec` 调用 `hydra` 或自定义脚本进行批量爆破。示例：`hydra -l admin -P /tmp/passwords.txt 10.255.1.2 http-get /login.php -s 81`。\n"
        "2. **注入探测**：使用 `kali_sqlmap` 进行 SQL 注入检测。通常先获取 --banner，然后 --dbs，最后 --dump。\n"
        "3. **信息收集**：使用 `kali_dirsearch` 进行目录爆破，分析页面寻找隐藏 Flag。\n\n"
        "**角色指令格式**：\n"
        "- 调用工具：CALL: kali_exec(cmd_str=\"...\")\n"
        "- 任务结束：FACTS: {\"password\": \"...\", \"cookie\": \"...\", \"vulnerabilities\": []}\n\n"
        "注意：严禁使用占位符，必须替换为真实的测试目标。"
    )
    
    graph = create_react_agent_graph(llm, tools, system_prompt=system_prompt)
    return graph
