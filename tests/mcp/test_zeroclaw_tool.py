import pytest
from unittest.mock import patch
from asas_mcp.tools.zeroclaw import zeroclaw_open_vnc

@pytest.mark.asyncio
async def test_zeroclaw_open_vnc_kali():
    with patch("asas_mcp.tools.zeroclaw.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "192.168.1.50\n"
        
        result = await zeroclaw_open_vnc("kali")
        
        assert "ZeroClaw browser launched" in result
        # Check if the correct NoVNC IP and port (6080) was passed
        mock_run.assert_any_call(
            ["zeroclaw", "agent", "-m", "打开浏览器访问 http://192.168.1.50:6080/vnc.html"],
            capture_output=True, text=True, check=False
        )
