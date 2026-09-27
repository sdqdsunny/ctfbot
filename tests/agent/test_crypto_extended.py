import pytest
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_crypto_extended_tools():
    llm = MockLLM()
    mcp_mock = AsyncMock()
    
    def side_effect(tool, args):
        if tool == "crypto_decode":
            content = args.get("content", "")
            # Morse code
            morse_map = {
                ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
                "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
                "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
                ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
                "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
                "--..": "Z"
            }
            if all(c in ".-/ " for c in content):
                decoded = "".join(morse_map.get(c, "?") for c in content.split())
                return decoded
            # Caesar
            if content.startswith("Khoor"):
                results = []
                for shift in range(26):
                    shifted = ""
                    for ch in content:
                        if ch.isalpha():
                            base = ord('A') if ch.isupper() else ord('a')
                            shifted += chr((ord(ch) - base + shift) % 26 + base)
                        else:
                            shifted += ch
                    results.append(f"Shift {shift}: {shifted}")
                return "\n".join(results)
            # Base64
            import base64
            try:
                return base64.b64decode(content).decode("utf-8")
            except:
                return content
        return "Unknown tool result"
    
    mcp_mock.call_tool.side_effect = side_effect
    app = create_agent_graph(llm, mcp_client=mcp_mock)
    
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
