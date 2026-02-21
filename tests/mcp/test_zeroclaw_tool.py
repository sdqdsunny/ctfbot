import pytest
from unittest.mock import patch
from asas_mcp.tools.zeroclaw import zeroclaw_open_vnc

@pytest.mark.asyncio
async def test_zeroclaw_open_vnc_kali():
    with patch("asas_mcp.tools.zeroclaw.subprocess.run") as mock_run:
        # Mock responses for subprocess.run
        # Call 1: vmrun list
        # Call 2: vmrun getGuestIPAddress
        # Call 3: zeroclaw agent ...
        def side_effect(args, **kwargs):
            if args[0] == "vmrun" and args[1] == "list":
                mock = type('obj', (object,), {'returncode': 0, 'stdout': 'Total running VMs: 1\n/path/to/kali.vmx'})()
                return mock
            elif args[0] == "vmrun" and args[1] == "getGuestIPAddress":
                mock = type('obj', (object,), {'returncode': 0, 'stdout': '192.168.1.50\n'})()
                return mock
            else: # zeroclaw command
                mock = type('obj', (object,), {'returncode': 0, 'stdout': '', 'stderr': ''})()
                return mock
                
        mock_run.side_effect = side_effect
        
        result = await zeroclaw_open_vnc("kali")
        
        assert "ZeroClaw browser launched" in result
        # Check if the correct NoVNC IP and port (6080) was passed
        mock_run.assert_any_call(
            ["zeroclaw", "agent", "-m", "打开浏览器访问 http://192.168.1.50:6080/vnc.html"],
            capture_output=True, text=True, check=False
        )
