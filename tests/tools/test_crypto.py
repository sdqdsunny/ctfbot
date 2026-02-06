from asas_mcp.tools import crypto

def test_decode_base64():
    encoded = "SGVsbG8gV29ybGQ="
    decoded = crypto.decode(encoded, method="base64")
    assert decoded == "Hello World"

def test_decode_hex():
    encoded = "48656c6c6f20576f726c64"
    decoded = crypto.decode(encoded, method="hex")
    assert decoded == "Hello World"
