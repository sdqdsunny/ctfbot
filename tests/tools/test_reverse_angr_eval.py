import pytest
import sys
from unittest.mock import MagicMock, patch

# Mock the entire angr and claripy module
if "angr" not in sys.modules:
    sys.modules["angr"] = MagicMock()
if "claripy" not in sys.modules:
    sys.modules["claripy"] = MagicMock()

from asas_mcp.tools.reverse_angr import reverse_angr_eval

@pytest.mark.asyncio
async def test_reverse_angr_eval_success():
    """验证 reverse_angr_eval 的解算逻辑"""
    import claripy
    
    # 模拟 claripy 的符号变量和求解器
    mock_solver = MagicMock()
    mock_x = MagicMock()
    
    # 设置 mock 行为
    claripy.Solver.return_value = mock_solver
    claripy.BVS.return_value = mock_x
    mock_solver.eval.return_value = [0x41424344]  # 模拟解出的值，返回列表
    
    result = await reverse_angr_eval.ainvoke({
        "expression": "x + 5 == 10",
        "symbolic_vars": {"x": 32}
    })
    
    assert "0x41424344" in result
    assert "Solution found" in result
