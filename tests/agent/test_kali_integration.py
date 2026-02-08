import pytest
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_kali_vm_integration_smoke():
    """
    Test that Agent can reach Kali VM tools.
    """
    llm = MockLLM()
    app = create_agent_graph(llm)
    
    # Simple Kali command
    inputs = {"user_input": "Run kali command: whoami"}
    result = await app.ainvoke(inputs)
    
    # The output of 'whoami' in the VM should be 'kali'
    assert "kali" in str(result["tool_result"]).strip()
    assert "whoami" in str(result["task_history"])
