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
async def test_reverse_agent_fuzz_e2e_flow():
    """验证 ReverseAgent 能够启动 Fuzzing 并分析崩溃"""
    
    mock_llm = MagicMock()
    
    # 模拟思维过程：
    # 1. 启动 Fuzzing
    ai_msg_1 = AIMessage(content="逻辑太复杂，我启动 Fuzzing。\nCALL: pwn_fuzz_start(binary_path='/tmp/pwnable', duration_sec=300)")
    # 2. 检查结果并发现崩溃
    ai_msg_2 = AIMessage(content="已经发现了崩溃。我开始自动化 Triage。\nCALL: pwn_fuzz_triage(container_id='cont_101', crash_filename='id:000')")
    # 3. 得到结论
    ai_msg_3 = AIMessage(content="分析显示这是一个典型的栈溢出漏洞。可以编写 Exploit 获取 Flag。")
    
    mock_llm.invoke.side_effect = [ai_msg_1, ai_msg_2, ai_msg_3]
    
    # Mocking the tools in the reverse module
    with patch("asas_agent.agents.reverse.pwn_fuzz_start") as mock_start, \
         patch("asas_agent.agents.reverse.pwn_fuzz_triage") as mock_triage:
        
        mock_start.name = "pwn_fuzz_start"
        mock_start.ainvoke = AsyncMock(return_value=json.dumps({"status": "started", "container_id": "cont_101"}))
        
        mock_triage.name = "pwn_fuzz_triage"
        mock_triage.ainvoke = AsyncMock(return_value="--- Crash Triage Report ---\nExploitable: YES\nVulnerability: Stack Overflow")
        
        agent_graph = create_reverse_agent(mock_llm, [])
        
        inputs = {"messages": [HumanMessage(content="帮我挖掘这个 /tmp/pwnable 的漏洞")]}
        result = await agent_graph.ainvoke(inputs)
        
        assert mock_start.ainvoke.called
        assert mock_triage.ainvoke.called
        assert "栈溢出" in result["messages"][-1].content
        print(f"✓ E2E Fuzzing integration verified. Findings: {result['messages'][-1].content}")
