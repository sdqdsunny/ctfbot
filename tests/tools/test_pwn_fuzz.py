import pytest
from unittest.mock import MagicMock, patch
from asas_mcp.tools.pwn_fuzz import pwn_fuzz_start, pwn_fuzz_triage

@pytest.mark.asyncio
async def test_pwn_fuzz_start():
    with patch("asas_mcp.tools.pwn_fuzz.get_docker_manager") as mock_get_dm:
        mock_dm = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "cont_123"
        mock_dm.start_fuzzer_container.return_value = mock_container
        mock_get_dm.return_value = mock_dm
        
        result = await pwn_fuzz_start.ainvoke({"binary_path": "/tmp/test", "duration_sec": 10})
        
        assert "started" in result
        assert "cont_123" in result
        assert mock_dm.exec_command.called

@pytest.mark.asyncio
async def test_pwn_fuzz_triage():
    with patch("asas_mcp.tools.pwn_fuzz.get_docker_manager") as mock_get_dm:
        mock_dm = MagicMock()
        mock_dm.exec_command.side_effect = [
            "test_bin in out", # ls /data
            "Description: Stack Buffer Overflow\nHash: 12345" # gdb triage
        ]
        mock_get_dm.return_value = mock_dm
        
        result = await pwn_fuzz_triage.ainvoke({
            "container_id": "cont_123",
            "crash_filename": "id:000,sig:11"
        })
        
        assert "Stack Buffer Overflow" in result
        assert "Report" in result
