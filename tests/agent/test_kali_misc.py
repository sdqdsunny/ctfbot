import pytest
from unittest.mock import AsyncMock, patch
from asas_agent.graph.workflow import create_agent_graph
from asas_agent.llm.mock import MockLLM

@pytest.mark.asyncio
async def test_kali_misc_tools_flow():
    """
    Test Misc tools flow (steghide, binwalk, foremost)
    """
    llm = MockLLM()
    mcp_mock = AsyncMock()
    
    def side_effect(tool, args):
        if tool == "kali_steghide":
            return "Steghide Output:\nwrote extracted data to \"steg_out.txt\"\n\nExtracted Content:\nflag{stego_found}"
        elif tool == "kali_binwalk":
            return "DECIMAL       HEXADUMP      DESCRIPTION\n--------------------------------------------------------------------------------\n0             0x0           PNG image\n100           0x64          Zip archive data"
        elif tool == "kali_foremost":
            return "Foremost Result:\n...\n\nExtracted Files:\noutput/png/000000.png"
        return "Unknown tool result"

    mcp_mock.call_tool.side_effect = side_effect
    
    with patch('asas_agent.mcp_client.client.MCPToolClient', return_value=mcp_mock):
        app = create_agent_graph(llm)
        
        # 1. Test Steghide
        res = await app.ainvoke({"user_input": "使用 steghide 检查文件 /tmp/secret.jpg"})
        assert "flag{stego_found}" in res["final_answer"]
        
        # 2. Test Binwalk
        res = await app.ainvoke({"user_input": "使用 binwalk 分析 /tmp/binary"})
        assert "Zip archive data" in res["final_answer"]
        
        # 3. Test Foremost
        res = await app.ainvoke({"user_input": "使用 foremost 恢复 /tmp/corrupted.img"})
        assert "Extracted Files" in res["final_answer"]
