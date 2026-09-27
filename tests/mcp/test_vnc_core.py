import pytest
from unittest.mock import AsyncMock, patch
from asas_mcp.tools.vnc_core import VNCHelper

@pytest.mark.asyncio
async def test_vnc_helper_initialization():
    helper = VNCHelper(host="127.0.0.1", port=5900)
    assert helper.host == "127.0.0.1"
    assert helper.port == 5900

@pytest.mark.asyncio
async def test_vnc_screenshot_mocked():
    helper = VNCHelper(host="127.0.0.1", port=5900)
    
    with patch("asas_mcp.tools.vnc_core.asyncvnc.connect") as mock_connect:
        mock_client = AsyncMock()
        mock_client.video.get_frame = AsyncMock(return_value=b"fake_raw_pixels")
        mock_connect.return_value.__aenter__.return_value = mock_client
        
        b64_img = await helper.take_screenshot()
        assert b64_img is not None
        assert isinstance(b64_img, str)
        mock_connect.assert_called_once()
        mock_client.video.get_frame.assert_called_once()

@pytest.mark.asyncio
async def test_vnc_mouse_click_mocked():
    helper = VNCHelper(host="127.0.0.1", port=5900)
    with patch("asas_mcp.tools.vnc_core.asyncvnc.connect") as mock_connect:
        mock_client = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_client
        
        result = await helper.mouse_click(100, 200)
        assert "success" in result.lower()
        mock_client.mouse.move.assert_called_with(100, 200)
        mock_client.mouse.click.assert_called()

@pytest.mark.asyncio
async def test_vnc_keyboard_type_mocked():
    helper = VNCHelper(host="127.0.0.1", port=5900)
    with patch("asas_mcp.tools.vnc_core.asyncvnc.connect") as mock_connect:
        mock_client = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_client
        
        result = await helper.keyboard_type("ls -la\n")
        assert "success" in result.lower()
        mock_client.keyboard.type.assert_called_with("ls -la\n")
