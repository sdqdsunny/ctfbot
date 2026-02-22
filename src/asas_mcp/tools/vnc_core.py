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
