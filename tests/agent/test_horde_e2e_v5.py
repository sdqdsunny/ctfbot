import pytest
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from asas_agent.agents.reverse import create_reverse_agent

# Mock ingredients
if "docker" not in sys.modules:
    sys.modules["docker"] = MagicMock()

@pytest.mark.asyncio
async def test_reverse_agent_horde_interop_e2e_flow():
    """验证 v5.5 Horde Interoperability: Fuzzing -> Stagnation -> Angr -> Injection"""
    
    mock_llm = MagicMock()
    
    # 模拟思维过程：
    # 1. 启动 Fuzzing
    m1 = AIMessage(content="目标疑似有深层逻辑，启动 Fuzzing。\nCALL: pwn_fuzz_start(binary_path='/tmp/horde_bin')")
    # 2. 检查进度，发现停滞 (total_paths 没增加)
    m2 = AIMessage(content="Fuzzing 停滞，开始提取种子进行符号解算。\nCALL: pwn_horde_get_seeds(container_id='cont_horde')")
    # 3. 使用种子辅助 Angr 解算
    m3 = AIMessage(content="基于种子前缀进行寻路。\nCALL: reverse_angr_solve(binary_path='/tmp/horde_bin', find_addr='0x401234', stdin_prefix_hex='414141')")
    # 4. 得到解并回灌
    m4 = AIMessage(content="Angr 找到了关键输入！回灌种子。\nCALL: pwn_horde_inject_seed(container_id='cont_horde', seed_hex='414141deadbeef')")
    # 5. 最终结论
    m5 = AIMessage(content="回灌后 Fuzzer 成功触发崩溃。分析显示是一个缓冲区溢出。任务完成。")
    
    mock_llm.invoke.side_effect = [m1, m2, m3, m4, m5]
    
    # Mock all the tools
    with patch("asas_agent.agents.reverse.pwn_fuzz_start") as t_start, \
         patch("asas_agent.agents.reverse.pwn_horde_get_seeds") as t_get, \
         patch("asas_agent.agents.reverse.reverse_angr_solve") as t_solve, \
         patch("asas_agent.agents.reverse.pwn_horde_inject_seed") as t_inject:
        
        t_start.name = "pwn_fuzz_start"
        t_start.ainvoke = AsyncMock(return_value=json.dumps({"status": "started", "container_id": "cont_horde"}))
        
        t_get.name = "pwn_horde_get_seeds"
        t_get.ainvoke = AsyncMock(return_value=json.dumps({"seeds": {"id:001": "414141"}}))
        
        t_solve.name = "reverse_angr_solve"
        t_solve.ainvoke = AsyncMock(return_value="Success! Found solution with prefix: 414141deadbeef")
        
        t_inject.name = "pwn_horde_inject_seed"
        t_inject.ainvoke = AsyncMock(return_value="Success: Seed injected.")
        
        agent_graph = create_reverse_agent(mock_llm, [])
        
        inputs = {"messages": [HumanMessage(content="利用 Horde 架构攻破 /tmp/horde_bin")]}
        result = await agent_graph.ainvoke(inputs)
        
        assert t_start.ainvoke.called
        assert t_get.ainvoke.called
        assert t_solve.ainvoke.called
        assert t_inject.ainvoke.called
        assert "缓冲区溢出" in result["messages"][-1].content
        print(f"✓ E2E Horde Interoperability verified. Cycle: Fuzz -> Angr -> Injection.")
