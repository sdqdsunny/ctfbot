import pytest
from asas_mcp.tools import sandbox

def test_sandbox_python_success():
    code = "print('hello from sandbox')"
    result = sandbox.run_python(code)
    assert "hello from sandbox" in result

def test_sandbox_network_blocked():
    # Attempting to ping google or open a socket should fail/timeout
    code = """
import socket
try:
    socket.create_connection(("8.8.8.8", 53), timeout=1)
    print("Network Access")
except:
    print("Network Blocked")
"""
    result = sandbox.run_python(code)
    assert "Network Blocked" in result

def test_sandbox_bash():
    code = "echo 'sh-sandbox'"
    result = sandbox.run_in_sandbox(code, "bash")
    assert "sh-sandbox" in result
