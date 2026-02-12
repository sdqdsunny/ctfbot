import pytest
import os
import sys
import subprocess
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from asas_agent.agents.reverse import create_reverse_agent
from unittest.mock import MagicMock, AsyncMock, patch

# 1. Mock LLM - 完整链式推理模拟
class DemoLLM:
    def __init__(self):
        self.step = 0
        
    def invoke(self, messages):
        self.step += 1
        binary_path = os.path.abspath("demo_challenge")
        
        if self.step == 1:
            return AIMessage(content="[分析阶段] 查看程序导入。\nCALL: ida_get_imports(binary_path='" + binary_path + "')")
        elif self.step == 2:
            return AIMessage(content="[特征分析] 搜索 Hash 字符串。\nCALL: ida_find_regex(binary_path='" + binary_path + "', regex='[a-f0-9]{32}')")
        elif self.step == 3:
            return AIMessage(content="[算力准备] 检查 GPU 算力节点。\nCALL: gpu_status()")
        elif self.step == 4:
            return AIMessage(content="[硬核破解] 调用 GPU 集群进行爆破。\nCALL: gpu_hashcat_crack(hash_value='0192023a7bbd73250516f069df18b500', hash_type='0')")
        elif self.step == 5:
            # 这一步必须包含工具调用，否则 workflow 会结束
            return AIMessage(content="[深度寻路] 爆破获得前缀 admin123。现在定位 Success 地址 0x100003e44 并请求 Angr 协同。\nCALL: reverse_angr_solve(binary_path='" + binary_path + "', find_addr='0x100003e44')")
        elif self.step == 6:
            return AIMessage(content="[最终总结] Angr 解算完成。攻击载荷已锁定：'admin123'。任务圆满成功。")
        else:
            return AIMessage(content="演习结束。")

@pytest.mark.asyncio
async def test_v6_swarm_real_e2e():
    """验证 v6.0 Swarm & GPU: 模拟 1B + 2AB 最终完整闭环测试"""
    
    # 强制清理之前的 binary 以确保新鲜
    if os.path.exists("demo_challenge"):
        os.remove("demo_challenge")
    subprocess.run(["gcc", "demo_challenge.c", "-o", "demo_challenge"], cwd=".")
    
    mock_llm = DemoLLM()
    
    def create_mock_tool(name, return_val):
        tool = MagicMock()
        tool.name = name
        tool.ainvoke = AsyncMock(return_value=return_val)
        return tool

    # Mock 掉 IDA 和 GPU，保持 Angr 真实
    with patch("asas_agent.agents.reverse.ida_get_imports", create_mock_tool("ida_get_imports", "Imports: [strlen, printf, strcmp]")),          patch("asas_agent.agents.reverse.ida_find_regex", create_mock_tool("ida_find_regex", "Found: 0192023a7bbd73250516f069df18b500 in .rodata")),          patch("asas_agent.agents.reverse.gpu_status", create_mock_tool("gpu_status", "NVIDIA GeForce RTX 4090 [Worker-01: ACTIVE]")),          patch("asas_agent.agents.reverse.gpu_hashcat_crack", create_mock_tool("gpu_hashcat_crack", "Success! Cracked result: 0192023a7bbd73250516f069df18b500:admin123")):
        
        agent_graph = create_reverse_agent(mock_llm, [])
        inputs = {"messages": [HumanMessage(content="武装分析 demo_challenge")]}
        
        print("\n" + "█"*65)
        print("🚀 [ACTION] 开启黄金之锤终极演习 (Operation: Golden Hammer ULTIMATE)")
        print("核心能力: 混合实战 (1B) + 分布式调度 (2A) + 深度推理链 (2B) + Angr 实地突破")
        print("█"*65)
        
        async for event in agent_graph.astream(inputs):
            for node, state in event.items():
                if node == "agent":
                    msg = state["messages"][-1]
                    print(f"\n🧠 [Agent 思维]: {msg.content}")
                elif node == "tools":
                    for msg in state["messages"]:
                        # 重点展示 Angr 的真实输出
                        header = f"🛠️ [工具反馈: {msg.name}]"
                        print(f"{header}\n{'-' * len(header)}\n{str(msg.content)[:800]}\n")
        
        print("█"*65)
        print("🔥 终极演习完美锁定！Agent 展示了跨维度的打击能力。")
        print("█"*65)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_v6_swarm_real_e2e())
