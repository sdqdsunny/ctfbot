import pytest
from unittest.mock import patch, Mock
from asas_mcp.tools.platform import platform_get_challenge, platform_submit_flag

@patch("requests.get")
def test_platform_get_challenge(mock_get):
    """Test fetching challenge from CTFd platform"""
    # Mock CTFd API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "name": "SQLi 101",
            "description": "Can you bypass the login?",
            "category": "Web"
        }
    }
    mock_get.return_value = mock_response
    
    result = platform_get_challenge("http://ctf.com/challenges/1", "token123")
    assert "SQLi 101" in result
    assert "Can you bypass the login?" in result
    mock_get.assert_called_once()

@patch("requests.post")
def test_platform_submit_flag(mock_post):
    """Test submitting flag to CTFd platform"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {"status": "correct"}
    }
    mock_post.return_value = mock_response
    
    result = platform_submit_flag(
        challenge_id="1",
        flag="flag{test}",
        base_url="http://ctf.com",
        token="token123"
    )
    assert "correct" in result.lower() or "success" in result.lower()
    mock_post.assert_called_once()
