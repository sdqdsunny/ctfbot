try:
    import ray
except ImportError:
    # Fallback for dev environment without Ray installed
    ray = None

import logging
import os
import platform
import psutil
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def remote_actor_decorator(cls):
    """Decorator to make the class a Ray actor if ray is available."""
    if ray:
        return ray.remote(cls)
    return cls

@remote_actor_decorator
class SwarmWorker:
    """
    A Ray Actor representing a remote worker node in the CTF-ASAS swarm.
    Each worker can execute tools, manage local Docker containers, and use local hardware.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.capabilities = self._detect_capabilities()
        self.task_history = [] # For reputation tracking
        logger.info(f"Worker {node_id} initialized with capabilities: {self.capabilities}")

    def _detect_capabilities(self) -> Dict[str, Any]:
        """Detect hardware and software capabilities of the node."""
        caps = {
            "os": platform.system(),
            "cpu_cores": psutil.cpu_count(logical=True),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "gpu": False,
            "gpu_info": None,
            "docker": False,
            "software": {
                "ida": False,
                "ghidra": False,
                "angr": False,
                "hashcat": False
            }
        }
        
        # 1. Detect Docker
        try:
            import docker
            client = docker.from_env()
            client.ping()
            caps["docker"] = True
        except Exception:
            pass

        # 2. Detect NVIDIA GPU
        try:
            output = subprocess.check_output(["nvidia-smi", "-L"], stderr=subprocess.STDOUT)
            if output:
                caps["gpu"] = True
                caps["gpu_info"] = output.decode().strip().split('\n')
        except Exception:
            pass

        # 3. Detect Software Stack
        # Check for IDA
        try:
            for cmd in ["ida64", "idat64"]:
                if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                    caps["software"]["ida"] = True
                    break
        except FileNotFoundError: pass
        
        # Check for Ghidra
        try:
            if os.environ.get("GHIDRA_PATH") or subprocess.run(["which", "ghidraRun"], capture_output=True).returncode == 0:
                caps["software"]["ghidra"] = True
        except FileNotFoundError: pass
            
        # Check for Angr
        try:
            import angr
            caps["software"]["angr"] = True
        except ImportError:
            pass
            
        # Check for Hashcat
        try:
            if subprocess.run(["hashcat", "--version"], capture_output=True).returncode == 0:
                caps["software"]["hashcat"] = True
        except FileNotFoundError:
            pass

        return caps

    def get_status(self) -> Dict[str, Any]:
        """Return the current status and capabilities of the worker."""
        return {
            "node_id": self.node_id,
            "capabilities": self.capabilities,
            "load": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "success_rate": self._calculate_success_rate()
        }

    def _calculate_success_rate(self) -> float:
        if not self.task_history:
            return 1.0 # New nodes are trusted
        successes = [t for t in self.task_history if t.get("success")]
        return len(successes) / len(self.task_history)

    async def execute_tool(self, tool_func_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on this remote node.
        """
        logger.info(f"Worker {self.node_id} executing tool: {tool_func_name}")
        
        # Prototype: record task for reputation
        task_record = {"tool": tool_func_name, "success": True}
        
        try:
            # Here we would dispatch to the real tool registry
            # For v6.0 prototype, we support simulated and some real tools via MCP
            result = f"Distributed Result from {self.node_id}: {tool_func_name} executed."
            return {"status": "success", "result": result}
        except Exception as e:
            task_record["success"] = False
            task_record["error"] = str(e)
            return {"status": "error", "message": str(e)}
        finally:
            self.task_history.append(task_record)
            if len(self.task_history) > 100: # Keep last 100 tasks
                self.task_history.pop(0)

    async def fetch_seeds(self, container_id: str) -> List[Dict[str, Any]]:
        """
        Fetch interesting seeds from a local fuzzer container.
        Returns a list of dicts with {filename: str, content_b64: str}
        """
        import base64
        try:
            from ..executors.docker_manager import get_docker_manager
            dm = get_docker_manager()
            # AFL++ structure: /data/out/default/queue/
            # We fetch all non-metadata files from the queue
            cmd = "find /data/out/default/queue/ -type f ! -name '.*'"
            files_iter = dm.exec_command(container_id, cmd).splitlines()
            
            seeds = []
            for file_path in files_iter:
                if not file_path: continue
                # Read file as base64 to handle binary seeds
                content_b64 = dm.exec_command(container_id, f"base64 {file_path}")
                seeds.append({
                    "filename": os.path.basename(file_path),
                    "content_b64": content_b64.strip()
                })
            return seeds
        except Exception as e:
            logger.error(f"Worker {self.node_id} failed to fetch seeds: {e}")
            return []

    async def inject_seeds(self, container_id: str, seeds: List[Dict[str, Any]]) -> int:
        """
        Inject foreign seeds into a local fuzzer container.
        """
        import base64
        try:
            from ..executors.docker_manager import get_docker_manager
            dm = get_docker_manager()
            count = 0
            for seed in seeds:
                # In AFL++, we usually inject into a separate sync directory 
                # or directly into the queue with a special prefix so we don't 
                # re-process what we already have. 
                # For simplicity, we put them in a 'sync' subfolder that AFL++ -S can pick up
                # Or just put them in /data/in for a restart.
                # Here we put them in /data/out/remote_sync/queue/
                sync_dir = "/data/out/remote_sync/queue"
                dm.exec_command(container_id, f"mkdir -p {sync_dir}")
                
                content = base64.b64decode(seed["content_b64"])
                # We need a way to write binary to container. 
                # DockerManager.exec_command usually takes a string. 
                # We'll use a hack for prototype: pipe base64 to file
                write_cmd = f"echo '{seed['content_b64']}' | base64 -d > {sync_dir}/{seed['filename']}"
                dm.exec_command(container_id, write_cmd)
                count += 1
            return count
        except Exception as e:
            logger.error(f"Worker {self.node_id} failed to inject seeds: {e}")
            return 0

    async def start_crack_job(self, job_args: Dict[str, Any]) -> bool:
        """
        Start or resume a hashcat job on this node.
        """
        logger.info(f"Worker {self.node_id} starting crack job: {job_args['job_id']}")
        try:
            # In a real implementation:
            # 1. Check for required wordlist, fetch if missing (via ResourceJanitor/SeedJanitor logic)
            # 2. Construct hashcat command (using --session for checkpointing)
            # 3. Launch process (docker or native)
            # 4. Store process handle
            
            # For prototype, we simulate success
            return True
        except Exception as e:
            logger.error(f"Failed to start crack job: {e}")
            return False

    async def pause_crack_job(self, job_id: str) -> str:
        """
        Pause a running hashcat job and return the checkpoint/restore data.
        """
        logger.info(f"Worker {self.node_id} pausing job {job_id}")
        try:
            # In real implementation:
            # 1. Send 'checkpoint' or 'quit' to hashcat session
            # 2. Wait for exit
            # 3. Read .restore file
            # 4. Return .restore file content as base64
            
            return "simulated_restore_data_base64"
        except Exception as e:
            logger.error(f"Failed to pause job: {e}")
            return ""
