import pytest
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from asas_agent.agents.reverse import create_reverse_agent

# Mock ingredients
if "docker" not in sys.modules:
    sys.modules["docker"] = MagicMock()
if "ray" not in sys.modules:
    sys.modules["ray"] = MagicMock()

@pytest.mark.asyncio
async def test_reverse_agent_v6_swarm_gpu_e2e_flow():
    """验证 v6.0 Swarm & GPU: 分布式节点发现与 GPU 爆破逻辑"""
    
    mock_llm = MagicMock()
    
    # 模拟思维过程：
    # 1. 检查集群状态
    m1 = AIMessage(content="我要开始大规模挖掘。先检查集群 GPU 算力。\nCALL: gpu_status()")
    # 2. 发现程序中有一个 MD5，启动 GPU 爆破
    m2 = AIMessage(content="发现硬编码 Hash: 5d41402abc4b2a76b9719d911017c592。启动 GPU 集群爆破。\nCALL: gpu_hashcat_crack(hash_value='5d41402abc4b2a76b9719d911017c592', hash_type='0')")
    # 3. 得到结果并得出结论
    m3 = AIMessage(content="GPU 成功爆破出密码: 'hello'。这是一个后门账户。任务完成。")
    
    mock_llm.invoke.side_effect = [m1, m2, m3]
    
    # Mocking tools
    with patch("asas_agent.agents.reverse.gpu_status") as t_status, \
         patch("asas_agent.agents.reverse.gpu_hashcat_crack") as t_crack:
        
        t_status.name = "gpu_status"
        t_status.ainvoke = AsyncMock(return_value="NVIDIA GeForce RTX 4090 [Active]")
        
        t_crack.name = "gpu_hashcat_crack"
        t_crack.ainvoke = AsyncMock(return_value="Success! Cracked result: 5d41402abc4b2a76b9719d911017c592:hello")
        
        agent_graph = create_reverse_agent(mock_llm, [])
        
        inputs = {"messages": [HumanMessage(content="帮我分析这个由于 Hash 校验卡住的程序")]}
        result = await agent_graph.ainvoke(inputs)
        
        assert t_status.ainvoke.called
        assert t_crack.ainvoke.called
        assert "hello" in result["messages"][-1].content
        print(f"✓ E2E v6.0 Swarm/GPU verification successful.")
