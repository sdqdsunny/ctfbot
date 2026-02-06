import pytest
from asas_mcp.tools import recon

def test_scan_basic():
    # Mocking would be used in real integration, but unit test checks function signature/return
    result = recon.scan(target="127.0.0.1", ports="80")
    assert "scan_result" in result
    assert result["target"] == "127.0.0.1"
