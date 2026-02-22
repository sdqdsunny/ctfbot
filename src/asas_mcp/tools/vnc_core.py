class VNCHelper:
    def __init__(self, host: str, port: int = 5900, password: str = None):
        self.host = host
        self.port = port
        self.password = password
        self._client = None
