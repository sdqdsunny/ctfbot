from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph
from asas_mcp.tools.ida_tools import (
    ida_decompile, ida_xrefs_to, ida_py_eval, 
    ida_list_funcs, ida_get_imports, ida_find_regex
)

def create_reverse_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Reverse Agent with IDA Pro support.
    """
    system_prompt = (
        "你是 CTF-ASAS 逆向工程专家 (ReverseAgent)。\n"
        "你拥有世界顶级的二进制分析能力，熟练使用 IDA Pro 和 Ghidra。\n\n"
        "你的主要职责：\n"
        "1. **深度分析**: 优先使用 `ida_` 系列工具。如果面临一个陌生的程序，推荐 SOP：\n"
        "   - 使用 `ida_get_imports` 查看程序依赖和可疑函数（如 system, exec, ptrace）。\n"
        "   - 使用 `ida_list_funcs` 获取全局概览。\n"
        "   - 使用 `ida_find_regex` 搜索 flag 格式或硬编码的密钥。\n"
        "   - 使用 `ida_decompile` 深入分析关键逻辑。\n"
        "2. **自动化求解**: 使用 `ida_py_eval` 在 IDA 环境内运行脚本，提取内存数据或解密算法。\n"
        "3. **灵活切换**: 如果 IDA 环境不可用（报错），降级使用 Ghidra 相关工具。\n\n"
        "目标：找到 Flag 并解释漏洞/逻辑点。输出结果必须专业且详实。"
    )
    
    # Bind IDA tools + existing tools
    ida_tools = [
        ida_decompile, ida_xrefs_to, ida_py_eval, 
        ida_list_funcs, ida_get_imports, ida_find_regex
    ]
    all_tools = tools + ida_tools
    
    graph = create_react_agent_graph(llm, all_tools, system_prompt=system_prompt)
    return graph
