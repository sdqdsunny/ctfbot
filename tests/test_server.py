import pytest
from asas_mcp.server import create_app

def test_server_creation():
    app = create_app()
    assert app is not None
