import ray
import logging
import os
import platform
import psutil
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

@ray.remote
class SwarmWorker:
    """
    A Ray Actor representing a remote worker node in the CTF-ASAS swarm.
    Each worker can execute tools, manage local Docker containers, and use local hardware.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.capabilities = self._detect_capabilities()
        logger.info(f"Worker {node_id} initialized with capabilities: {self.capabilities}")

    def _detect_capabilities(self) -> Dict[str, Any]:
        """Detect hardware and software capabilities of the node."""
        caps = {
            "os": platform.system(),
            "cpu_cores": psutil.cpu_count(logical=True),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "gpu": False,
            "gpu_info": None,
            "docker": False
        }
        
        # Detect Docker
        try:
            import docker
            client = docker.from_env()
            client.ping()
            caps["docker"] = True
        except Exception:
            pass

        # Detect NVIDIA GPU (Simplified check)
        try:
            import subprocess
            output = subprocess.check_output(["nvidia-smi", "-L"], stderr=subprocess.STDOUT)
            if output:
                caps["gpu"] = True
                caps["gpu_info"] = output.decode().strip().split('\n')
        except Exception:
            pass

        return caps

    def get_status(self) -> Dict[str, Any]:
        """Return the current status and capabilities of the worker."""
        return {
            "node_id": self.node_id,
            "capabilities": self.capabilities,
            "load": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }

    async def execute_tool(self, tool_func_name: str, args: Dict[str, Any]) -> str:
        """
        Execute a tool on this remote node.
        Note: The actual tool function must be available in the worker's environment.
        """
        logger.info(f"Worker {self.node_id} executing tool: {tool_func_name} with args {args}")
        # In a real implementation, this would look up the tool in a registry
        # and invoke it. For v6.0 prototype, we handle specific logic or dispatch.
        return f"Result from worker {self.node_id} for tool {tool_func_name}"

    def get_plasma_object(self, object_id: ray.ObjectRef):
        """Retrieve an object from the global Plasma store."""
        return ray.get(object_id)
