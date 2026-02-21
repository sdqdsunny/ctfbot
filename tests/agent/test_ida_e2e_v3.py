import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from asas_agent.graph.workflow import create_orchestrator_graph
from asas_agent.agents.reverse import create_reverse_agent
from langchain_core.tools import tool

@pytest.mark.skip(reason="需要 IDA Pro 服务器和多 Agent 协作图环境")
@pytest.mark.asyncio
async def test_orchestrator_to_reverse_ida_flow():
    """
    Test the multi-agent flow where Orchestrator dispatches a reverse challenge
    and ReverseAgent uses IDA tools.
    """
    
    # 1. Mock the LLMs
    mock_orchestrator_llm = MagicMock()
    mock_reverse_llm = MagicMock()
    
    # 2. Mock Orchestrator's responses: first dispatch, then finish
    orchestrator_ai_msg_1 = AIMessage(
        content="这是一个逆向题目，我需要分配给逆向专家。\nCALL: dispatch_to_agent(agent_type='reverse', task='分析这个二进制文件并找到 flag', platform_url='http://ctf.local')"
    )
    orchestrator_ai_msg_2 = AIMessage(
        content="子代理成功取回了 Flag：flag{ida_pro_is_awesome}。任务完成。"
    )
    mock_orchestrator_llm.invoke.side_effect = [orchestrator_ai_msg_1, orchestrator_ai_msg_2]
    
    # 3. Mock ReverseAgent's responses
    reverse_ai_msg_1 = AIMessage(content="我先看看导入表。\nCALL: ida_get_imports()")
    reverse_ai_msg_2 = AIMessage(content="发现 printf。搜一下 flag。\nCALL: ida_find_regex(pattern='flag{.*}')")
    reverse_ai_msg_3 = AIMessage(content="找到了！Flag 是 flag{ida_pro_is_awesome}。")
    mock_reverse_llm.invoke.side_effect = [reverse_ai_msg_1, reverse_ai_msg_2, reverse_ai_msg_3]
    
    # 4. Define Mock dispatch tool
    @tool
    async def dispatch_to_agent(agent_type: str, task: str, **kwargs):
        """Mock dispatch tool that runs our mock sub-agent."""
        if agent_type == "reverse":
            # The ida tools used by ReverseAgent need to be mocked at the client level
            with patch("asas_mcp.tools.ida_tools.get_ida_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_get_client.return_value = mock_client
                
                # Setup tool results for the client
                mock_client.execute_tool.side_effect = [
                    {"libc.so.6": ["printf", "strcmp"]}, # for ida_get_imports
                    [{"addr": "0x402010", "match": "flag{ida_pro_is_awesome}"}] # for ida_find_regex
                ]
                
                # Create the reverse agent graph
                # Note: ReverseAgent internally binds IDA tools
                reverse_graph = create_reverse_agent(mock_reverse_llm, [])
                
                # Invoke sub-agent
                result = await reverse_graph.ainvoke({"messages": [HumanMessage(content=task)]})
                
                # Return standardized JSON (matching AgentResult format from dispatcher)
                return json.dumps({
                    "status": "success",
                    "flag": "flag{ida_pro_is_awesome}",
                    "reasoning": result["messages"][-1].content,
                    "extracted_facts": {"flag": "flag{ida_pro_is_awesome}"}
                })
        return "Unknown agent"

    # 5. Setup and Run Orchestrator
    orchestrator_tools = [dispatch_to_agent]
    orchestrator_graph = create_orchestrator_graph(mock_orchestrator_llm, orchestrator_tools)
    
    inputs = {"messages": [HumanMessage(content="帮我做一下这个逆向题")]}
    result = await orchestrator_graph.ainvoke(inputs)
    
    # 6. Verifications
    assert mock_orchestrator_llm.invoke.called
    final_content = str(result["messages"][-1].content)
    assert "flag{ida_pro_is_awesome}" in final_content
    print(f"✓ E2E Flow verified. Found Flag: {final_content}")
