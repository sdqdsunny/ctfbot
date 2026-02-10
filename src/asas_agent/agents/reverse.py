from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph
from ...asas_mcp.tools.ida_tools import ida_decompile, ida_xrefs_to, ida_py_eval

def create_reverse_agent(llm, tools: List[BaseTool]):
    """
    Create a specialized Reverse Agent with IDA Pro support.
    """
    system_prompt = (
        "你是 CTF-ASAS 逆向工程专家 (ReverseAgent)。\n"
        "你拥有世界顶级的二进制分析能力，熟练使用 IDA Pro 和 Ghidra。\n\n"
        "你的主要职责：\n"
        "1. **深度分析**: 优先使用 `ida_decompile` 和 `ida_xrefs_to` 分析程序逻辑。\n"
        "2. **逆向 SOP**:\n"
        "   - 启动后执行 `ida_auto_analyze` (通过 py_eval 调用) 确保分析完成。\n"
        "   - 搜索关键字符串 (flag, correct, key) 并追踪其引用。\n"
        "   - 分析校验逻辑，识别加密算法 (AES, TEA, RC4 等)。\n"
        "3. **自动化求解**: 使用 `ida_py_eval` 在 IDA 环境内运行脚本，提取内存数据或解密算法。\n"
        "4. **灵活切换**: 如果 IDA 环境不可用，降级使用 Ghidra 相关工具。\n\n"
        "目标：找到 Flag 并解释漏洞/逻辑点。"
    )
    
    # Bind IDA tools + existing tools
    ida_tools = [ida_decompile, ida_xrefs_to, ida_py_eval]
    all_tools = tools + ida_tools
    
    graph = create_react_agent_graph(llm, all_tools, system_prompt=system_prompt)
    return graph
