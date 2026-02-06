import base64

def decode(content: str, method: str = "auto") -> str:
    if method == "base64":
        return base64.b64decode(content).decode('utf-8')
    # Add auto-detection logic later
    return content
