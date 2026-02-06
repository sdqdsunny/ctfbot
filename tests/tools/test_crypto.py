from asas_mcp.tools import crypto

def test_decode_base64():
    encoded = "SGVsbG8gV29ybGQ="
    decoded = crypto.decode(encoded, method="base64")
    assert decoded == "Hello World"
