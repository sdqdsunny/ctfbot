import pytest
from asas_mcp.tools.vnc_core import VNCHelper

@pytest.mark.asyncio
async def test_vnc_helper_initialization():
    helper = VNCHelper(host="127.0.0.1", port=5900)
    assert helper.host == "127.0.0.1"
    assert helper.port == 5900
