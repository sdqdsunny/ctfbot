from typing import List
from langchain_core.tools import BaseTool
from ..graph.workflow import create_react_agent_graph
from asas_mcp.tools.ida_tools import (
    ida_decompile, ida_xrefs_to, ida_py_eval, 
    ida_list_funcs, ida_get_imports, ida_find_regex
)
from asas_mcp.tools.reverse_angr import reverse_angr_solve, reverse_angr_eval
from asas_mcp.tools.pwn_fuzz import pwn_fuzz_start, pwn_fuzz_check, pwn_fuzz_triage

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
        "2. **符号寻路 (Guided Hunting)**: 当你在 IDA 中发现关键校验、'Success' 提示或特定的 Flag 校验函数时：\n"
        "   - 获取该逻辑分支或打印成功信息的地址。\n"
        "   - 调用 `reverse_angr_solve` 自动解算能够到达该地址的输入内容。\n"
        "3. **方程破解**: 如果遇到复杂的数学方程或校验算法，将其简化并使用 `reverse_angr_eval` 进行离线求解。\n"
        "4. **漏洞挖掘 (Swarm Fuzzing)**: 如果二进制文件逻辑过于复杂或疑似存在内存破坏漏洞（Pwn）：\n"
        "   - 使用 `pwn_fuzz_start` 启动后台分布式 Fuzzer。\n"
        "   - 定期使用 `pwn_fuzz_check` 观察分析进度。\n"
        "   - 发现 Crash 后，立即调用 `pwn_fuzz_triage` 获取自动化分析报告，定位溢出位置与原理。\n"
        "5. **自动化求解**: 使用 `ida_py_eval` 在 IDA 环境内运行脚本，提取内存数据或解密算法。\n"
        "6. **灵活切换**: 如果 IDA 环境不可用（报错），降级使用 Ghidra 相关工具。\n\n"
        "目标：找到 Flag 并解释漏洞/逻辑点。输出结果必须专业且详实。"
    )
    
    # Bind IDA + Angr + Fuzz tools + existing tools
    ida_tools = [
        ida_decompile, ida_xrefs_to, ida_py_eval, 
        ida_list_funcs, ida_get_imports, ida_find_regex
    ]
    angr_tools = [reverse_angr_solve, reverse_angr_eval]
    fuzz_tools = [pwn_fuzz_start, pwn_fuzz_check, pwn_fuzz_triage]
    all_tools = tools + ida_tools + angr_tools + fuzz_tools
    
    graph = create_react_agent_graph(llm, all_tools, system_prompt=system_prompt)
    return graph
