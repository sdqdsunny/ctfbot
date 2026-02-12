import pytest
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from asas_agent.agents.reverse import create_reverse_agent

# Mock components that require standard environments
if "angr" not in sys.modules:
    sys.modules["angr"] = MagicMock()
if "claripy" not in sys.modules:
    sys.modules["claripy"] = MagicMock()

@pytest.mark.asyncio
async def test_reverse_agent_angr_e2e_flow():
    """验证 ReverseAgent 能够主动使用 Angr 解决路径寻址任务"""
    
    mock_llm = MagicMock()
    
    # 1. 模拟 Agent 的思考过程
    # 第一步：发现可疑字符串
    ai_msg_1 = AIMessage(content="发现 'Correct' 字符串位于 0x401234。我将尝试使用 Angr 寻找输入路径。\nCALL: reverse_angr_solve(binary_path='/tmp/bin', find_addr='0x401234')")
    # 第二步：获取 Angr 结果后成功找到 Flag
    ai_msg_2 = AIMessage(content="Angr 返回结果：'passwd_123'。这就是 Flag。")
    
    mock_llm.invoke.side_effect = [ai_msg_1, ai_msg_2]
    
    # 2. 模拟 Angr 工具的输出
    # 我们 Patch 掉导入到 reverse 模块中的工具对象
    with patch("asas_agent.agents.reverse.reverse_angr_solve") as mock_angr_tool:
        mock_angr_tool.name = "reverse_angr_solve"
        mock_angr_tool.ainvoke = AsyncMock(return_value="Success! Path found. Input reaching 0x401234:\npasswd_123")
        mock_angr_tool.return_value = "Success! Path found. Input reaching 0x401234:\npasswd_123"
        
        # 3. 创建 Agent 并跑通 Graph
        agent_graph = create_reverse_agent(mock_llm, [])
        
        inputs = {"messages": [HumanMessage(content="分析这个 /tmp/bin 文件并找到输入")]}
        result = await agent_graph.ainvoke(inputs)
        
        # 4. 验证链路
        # 验证工具的 ainvoke 是否被调用
        assert mock_angr_tool.ainvoke.called
        # 验证最终输出包含解算出的内容
        assert "passwd_123" in result["messages"][-1].content
        print(f"✓ E2E Angr integration verified. Solving input: {result['messages'][-1].content}")
