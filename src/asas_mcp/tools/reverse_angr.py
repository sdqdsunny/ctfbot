from typing import List, Optional
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool
async def reverse_angr_solve(binary_path: str, find_addr: str, avoid_addrs: Optional[List[str]] = None) -> str:
    """
    使用 Angr 符号执行查找二进制文件中的特定路径（目标地址）。
    
    Args:
        binary_path: 需要分析的二进制文件路径。
        find_addr: 目标地址（十六进制字符串，如 '0x401234'）。
        avoid_addrs: 需要避开的地址列表（可选）。
        
    Returns:
        解算出的输入内容（Stdin）或错误信息。
    """
    try:
        import angr
    except ImportError:
        return "Error: 'angr' library is not installed. Please install it to use this tool."

    try:
        # 1. 初始化项目
        project = angr.Project(binary_path, auto_load_libs=False)
        
        # 2. 从入口点开始建立初始状态
        state = project.factory.entry_state()
        
        # 3. 创建仿真管理器
        simgr = project.factory.simgr(state)
        
        # 4. 转换地址格式
        target_addr = int(find_addr, 16)
        avoid_list = [int(a, 16) for a in (avoid_addrs or [])]
        
        # 5. 执行搜索
        print(f"DEBUG [Angr]: Exploring path to {find_addr}...")
        simgr.explore(find=target_addr, avoid=avoid_list)
        
        # 6. 处理结果
        if simgr.found:
            found_state = simgr.found[0]
            # 提取 Stdin 产生的输入
            solution = found_state.posix.dumps(0)
            try:
                decoded_solution = solution.decode('utf-8')
            except:
                decoded_solution = str(solution)
                
            return f"Success! Path found. Input reaching {find_addr}:\n{decoded_solution}"
        else:
            return f"Could not find a path to {find_addr}. Explored {len(simgr.deadended)} deadends."
            
    except Exception as e:
        logger.error(f"Angr execution failed: {e}")
        return f"Error during Angr execution: {str(e)}"
@tool
async def reverse_angr_eval(expression: str, symbolic_vars: dict) -> str:
    """
    使用 Angr/Claripy 解算独立的符号表达式或方程。
    
    Args:
        expression: Python 风格的表达式字符串，如 'x + 5 == 10'。
        symbolic_vars: 变量名及其位宽的映射，如 {'x': 32}。
        
    Returns:
        满足条件的变量解。
    """
    try:
        import claripy
    except ImportError:
        return "Error: 'claripy' library is not installed. Please install it to use this tool."

    try:
        solver = claripy.Solver()
        
        # 1. 创建符号变量
        vars_map = {}
        for name, bits in symbolic_vars.items():
            vars_map[name] = claripy.BVS(name, bits)
            
        # 2. 构建并添加约束
        # 安全注意：这里使用的是 eval。由于这是在受控的分析环境中，
        # 并且输入由 Agent 产生，我们暂时信任此行为，但理想情况下应用解析库。
        # 这里我们将 vars_map 作为 globals 传入 eval
        constraint = eval(expression, {"__builtins__": None}, vars_map)
        solver.add(constraint)
        
        # 3. 求解
        if solver.satisfiable():
            results = {}
            for name, var in vars_map.items():
                val = solver.eval(var, 1)[0]
                results[name] = hex(val)
                
            return f"Solution found!\n{results}"
        else:
            return "Unsatisifiable: No solution exists for the given constraints."
            
    except Exception as e:
        return f"Error during evaluation: {str(e)}"
