import pytest
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_crypto_extended_tools():
    llm = MockLLM()
    app = create_agent_graph(llm)
    
    # Test Morse
    inputs_morse = {"user_input": "Decode Morse: .... . .-.. .-.. ---"}
    result_morse = await app.ainvoke(inputs_morse)
    assert "HELLO" in str(result_morse["final_answer"])

    # Test Caesar (Should try all shifts)
    inputs_caesar = {"user_input": "凯撒加密: Khoor 123"}
    result_caesar = await app.ainvoke(inputs_caesar)
    assert "Shift 23: Hello 123" in str(result_caesar["final_answer"])
    
    # Test Auto-detect Base64
    inputs_auto = {"user_input": "解码: SGVsbG8="}
    result_auto = await app.ainvoke(inputs_auto)
    assert "Hello" in str(result_auto["final_answer"])
