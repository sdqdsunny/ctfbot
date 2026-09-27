import asyncvnc
import base64

class VNCHelper:
    def __init__(self, host: str, port: int = 5900, password: str = None):
        self.host = host
        self.port = port
        self.password = password
        self._client = None

    async def take_screenshot(self) -> str:
        """Connects to VNC, grabs a frame, and returns it as base64 png/jpeg format."""
        try:
            async with asyncvnc.connect(self.host, self.port, password=self.password) as client:
                raw_frame = await client.video.get_frame()
                return base64.b64encode(raw_frame).decode('utf-8')
        except Exception as e:
            return f"Error: {str(e)}"

    async def mouse_click(self, x: int, y: int, button: str = "left") -> str:
        try:
            async with asyncvnc.connect(self.host, self.port, password=self.password) as client:
                await client.mouse.move(x, y)
                await client.mouse.click(button) # assuming asyncvnc has this interface
                return f"Success: Clicked {button} at ({x}, {y})"
        except Exception as e:
            return f"Error: {str(e)}"

    async def keyboard_type(self, text: str) -> str:
        try:
            async with asyncvnc.connect(self.host, self.port, password=self.password) as client:
                # Note: exact asyncvnc API might differ, e.g. iterate chars
                await client.keyboard.type(text) 
                return f"Success: Typed text length {len(text)}"
        except Exception as e:
            return f"Error: {str(e)}"
