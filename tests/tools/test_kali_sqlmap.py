import pytest
from unittest.mock import patch, MagicMock
from asas_mcp.tools.kali_sqlmap import run_sqlmap_scan

@pytest.mark.asyncio
async def test_run_sqlmap_scan():
    # Mock subprocess.run or docker client
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "Target is injectable... current user: 'root'"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = await run_sqlmap_scan(url="http://test.local/sqli?id=1")
        
        assert "root" in result
        # Verify docker command structure
        args = mock_run.call_args[0][0]
        assert "docker" in args
        assert "exec" in args
        assert "ctfbot-kali" in args
        assert "sqlmap" in args
