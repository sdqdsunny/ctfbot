import pytest
from unittest.mock import MagicMock, patch
from asas_mcp.executors.docker_manager import DockerManager

def test_docker_manager_init():
    with patch("docker.from_env") as mock_env:
        manager = DockerManager()
        assert mock_env.called

def test_start_fuzzer_container():
    with patch("docker.from_env") as mock_env:
        mock_client = MagicMock()
        mock_env.return_value = mock_client
        manager = DockerManager()
        
        manager.start_fuzzer_container("/tmp/test_bin", "test_fuzzer")
        
        # 验证是否调用了 containers.run
        assert mock_client.containers.run.called
        args, kwargs = mock_client.containers.run.call_args
        assert args[0] == "ctf-asas-fuzzer"
        assert "volumes" in kwargs
        assert "/tmp" in str(kwargs["volumes"])
