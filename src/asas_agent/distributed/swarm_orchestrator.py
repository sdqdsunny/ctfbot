try:
    import ray
except ImportError:
    ray = None
import logging
from typing import List, Dict, Any
from .swarm_worker import SwarmWorker

logger = logging.getLogger(__name__)

class SwarmOrchestrator:
    """
    Manages the pool of SwarmWorkers via Ray.
    """
    def __init__(self, address: str = "auto"):
        if not ray.is_initialized():
            ray.init(address=address, ignore_reinit_error=True)
        self.workers: List[ray.actor.ActorHandle] = []

    def discover_workers(self) -> int:
        """
        In a real Ray cluster, workers are added to the cluster externally.
        This method would instantiate the SwarmWorker actor on available Ray nodes.
        """
        # For prototype, we create 3 local workers if none exist
        if not self.workers:
            for i in range(3):
                worker = SwarmWorker.remote(f"node-{i}")
                self.workers.append(worker)
        return len(self.workers)

    async def get_cluster_status(self) -> List[Dict[str, Any]]:
        """Gather status from all worker nodes."""
        status_refs = [worker.get_status.remote() for worker in self.workers]
        return await ray.get(status_refs)

    async def dispatch_to_best_worker(self, tool_name: str, args: Dict[str, Any], require_gpu: bool = False) -> str:
        """
        Simple scheduling logic: find a worker with requested capabilities and lowest load.
        """
        statuses = await self.get_cluster_status()
        
        eligible_workers = []
        for i, status in enumerate(statuses):
            if require_gpu and not status["capabilities"]["gpu"]:
                continue
            eligible_workers.append((i, status))
        
        if not eligible_workers:
            return f"Error: No worker available with capabilities (GPU={require_gpu})"
        
        # Sort by load
        eligible_workers.sort(key=lambda x: x[1]["load"])
        best_worker_idx = eligible_workers[0][0]
        
        return await self.workers[best_worker_idx].execute_tool.remote(tool_name, args)

_orchestrator = None
def get_swarm_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SwarmOrchestrator()
    return _orchestrator
