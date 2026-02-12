import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Mock the entire angr module before importing the tool if it's not present
if "angr" not in sys.modules:
    mock_angr = MagicMock()
    sys.modules["angr"] = mock_angr

from asas_mcp.tools.reverse_angr import reverse_angr_solve

@pytest.mark.asyncio
async def test_reverse_angr_solve_success():
    """验证 reverse_angr_solve 工具在成功找到路径时的行为"""
    # 模拟 angr 的项目和仿真管理器的复杂链式调用
    mock_project = MagicMock()
    mock_simgr = MagicMock()
    mock_found_state = MagicMock()
    
    # 设置 mock 链: Project -> factory.entry_state -> simgr -> explore -> found[0].posix.dumps(0)
    mock_project.factory.entry_state.return_value = MagicMock()
    mock_project.factory.simgr.return_value = mock_simgr
    mock_simgr.found = [mock_found_state]
    mock_found_state.posix.dumps.return_value = b"flag{test_angr_input}"
    
    with patch("angr.Project", return_value=mock_project):
        # 执行测试
        result = await reverse_angr_solve.ainvoke({
            "binary_path": "/tmp/dummy_bin",
            "find_addr": "0x401234"
        })
        
        # 验证结果
        assert "flag{test_angr_input}" in result
        assert "Success" in result

@pytest.mark.asyncio
async def test_reverse_angr_solve_no_path():
    """验证 reverse_angr_solve 在未找到路径时的处理"""
    mock_project = MagicMock()
    mock_simgr = MagicMock()
    mock_simgr.found = []  # 未找到任何路径
    
    mock_project.factory.simgr.return_value = mock_simgr
    
    with patch("angr.Project", return_value=mock_project):
        result = await reverse_angr_solve.ainvoke({
            "binary_path": "/tmp/dummy_bin",
            "find_addr": "0xdeadbeef"
        })
        
        assert "Could not find" in result
