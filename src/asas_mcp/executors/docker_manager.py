import docker
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class DockerManager:
    """
    负责管理 Fuzzing 容器的生命周期。
    支持分布式环境 (通过 remote_host)。
    """
    def __init__(self, remote_host: Optional[str] = None):
        try:
            if remote_host:
                self.client = docker.DockerClient(base_url=remote_host)
            else:
                self.client = docker.from_env()
        except Exception as e:
            logger.error(f"无法连接到 Docker 守护进程: {e}")
            self.client = None
        self._container_mounts = {} # container_id -> host_binary_dir

    def build_fuzzer_image(self, dockerfile_path: str, tag: str = "ctf-asas-fuzzer"):
        """从 Dockerfile 构建 Fuzzer 镜像"""
        if not self.client: return False
        
        logger.info(f"正在构建 Docker 镜像 {tag}...")
        path = os.path.dirname(dockerfile_path)
        dockerfile = os.path.basename(dockerfile_path)
        
        try:
            image, logs = self.client.images.build(path=path, dockerfile=dockerfile, tag=tag)
            for line in logs:
                if 'stream' in line:
                    logger.debug(line['stream'].strip())
            return True
        except Exception as e:
            logger.error(f"镜像构建失败: {e}")
            return False

    def start_fuzzer_container(self, binary_path: str, container_name: str = None):
        """启动一个 Fuzzer 容器并将二进制文件挂载进去"""
        if not self.client: return None
        
        # 提取二进制文件目录以挂载
        abs_binary_path = os.path.abspath(binary_path)
        binary_dir = os.path.dirname(abs_binary_path)
        binary_name = os.path.basename(abs_binary_path)
        
        volumes = {
            binary_dir: {'bind': '/data', 'mode': 'rw'}
        }
        
        try:
            container = self.client.containers.run(
                "ctf-asas-fuzzer",
                detach=True,
                name=container_name,
                volumes=volumes,
                tty=True,
                stdin_open=True,
                cap_add=["SYS_PTRACE"] # 允许调试
            )
            self._container_mounts[container.id] = binary_dir
            logger.info(f"容器 {container.short_id} 已启动，挂载点: /data/{binary_name}")
            return container
        except Exception as e:
            logger.error(f"启动容器失败: {e}")
            return None

    def exec_command(self, container_id: str, command: str):
        """在运行中的容器内执行指令"""
        if not self.client: return "Error: Docker not available"
        
        try:
            container = self.client.containers.get(container_id)
            exit_code, output = container.exec_run(command)
            return output.decode('utf-8')
        except Exception as e:
            return f"Error executing command: {e}"

    def stop_container(self, container_id: str):
        """停止并移除容器"""
        if not self.client: return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            if container_id in self._container_mounts:
                del self._container_mounts[container_id]
            return True
        except Exception as e:
            logger.warning(f"移除容器失败: {e}")
            return False

    def list_files(self, container_id: str, directory: str) -> List[str]:
        """列出容器内指定目录的文件"""
        output = self.exec_command(container_id, f"ls -1 {directory}")
        if "Error" in output: return []
        return [f.strip() for f in output.split("\n") if f.strip()]

    def read_file(self, container_id: str, file_path: str) -> Optional[bytes]:
        """从容器内读取文件内容（Base64 传输以支持二进制）"""
        import base64
        cmd = f"base64 {file_path}"
        output = self.exec_command(container_id, cmd)
        if "Error" in output or "base64:" in output:
            return None
        try:
            return base64.b64decode(output)
        except Exception:
            return None

    def write_file(self, container_id: str, file_path: str, content: bytes):
        """将内容写入容器内文件"""
        import base64
        encoded = base64.b64encode(content).decode('ascii')
        cmd = f"bash -c 'echo {encoded} | base64 -d > {file_path}'"
        self.exec_command(container_id, cmd)

_manager = None
def get_docker_manager():
    global _manager
    if _manager is None:
        _manager = DockerManager()
    return _manager
