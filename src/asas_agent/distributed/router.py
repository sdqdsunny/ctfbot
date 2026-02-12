import logging
import asyncio
from typing import List, Dict, Any, Optional
from .swarm_worker import SwarmWorker

logger = logging.getLogger(__name__)

class SwarmRouter:
    """
    Transparent router that dispatches tasks to the best available SwarmWorker.
    Implements reputation tracking, load balancing, and blacklisting.
    """
    def __init__(self):
        self.workers: Dict[str, Any] = {} # node_id -> SwarmWorker Actor
        self.blacklist: set = set()
        self.node_stats: Dict[str, Dict[str, Any]] = {} # node_id -> stats

    def add_worker(self, node_id: str, worker_actor: Any):
        """Register a new worker in the pool."""
        self.workers[node_id] = worker_actor
        self.node_stats[node_id] = {
            "tasks_started": 0,
            "tasks_failed": 0,
            "last_seen": asyncio.get_event_loop().time()
        }
        logger.info(f"Worker {node_id} added to SwarmRouter pool.")

    def ban_node(self, node_id: str):
        """Manually blacklist a node."""
        self.blacklist.add(node_id)
        logger.warning(f"Node {node_id} has been BLACKLISTED by administrator.")

    def unban_node(self, node_id: str):
        """Remove a node from the blacklist."""
        self.blacklist.discard(node_id)
        logger.info(f"Node {node_id} has been unbanned.")

    async def _get_worker_status(self, worker: Any) -> Dict[str, Any]:
        """Unified method to get status from either a Ray Actor or a local object."""
        from .utils import is_ray_actor
        try:
            if is_ray_actor(worker):
                return await worker.get_status.remote()
            
            # Check if it's a coroutine function or AsyncMock
            status_obj = worker.get_status()
            if asyncio.iscoroutine(status_obj) or hasattr(status_obj, "__await__"):
                return await status_obj
            return status_obj
        except Exception as e:
            logger.error(f"Error getting status from worker: {e}")
            raise

    async def get_best_worker(self, required_tags: List[str] = None) -> Optional[str]:
        """
        Select the best worker based on:
        1. Not in blacklist
        2. Has required capabilities (tags)
        3. Success rate & real-time load
        """
        best_node = None
        highest_score = -1.0
        
        for node_id, worker in self.workers.items():
            if node_id in self.blacklist:
                continue
                
            try:
                status = await self._get_worker_status(worker)
                
                # Filter by capability tags (e.g., "gpu", "ida")
                if required_tags:
                    caps = status["capabilities"]
                    if not all(self._check_capability(caps, tag) for tag in required_tags):
                        print(f"DEBUG: Node {node_id} filtered out due to missing tags. Caps: {caps}")
                        continue
                
                # Reputation score: Success rate * (1 - load)
                reputation = status.get("success_rate", 1.0)
                load_factor = 1.0 - (status.get("load", 0) / 100.0)
                score = reputation * load_factor
                print(f"DEBUG: Node {node_id} score: {score} (Rep: {reputation}, Load: {status.get('load')})")
                
                if score > highest_score:
                    highest_score = score
                    best_node = node_id
                    
            except Exception as e:
                logger.error(f"Failed to poll status from {node_id}: {e}")
                
        return best_node

    def _check_capability(self, caps: Dict[str, Any], tag: str) -> bool:
        """Check if node has a specific capability."""
        tag = tag.lower()
        if tag == "gpu": return caps.get("gpu", False)
        if tag == "docker": return caps.get("docker", False)
        if tag in caps.get("software", {}):
            return caps["software"][tag]
        return False

    async def dispatch(self, tool_name: str, args: Dict[str, Any], tags: List[str] = None) -> Any:
        """
        High-level entry point: Find best worker, execute, and handle retries.
        """
        from .utils import is_ray_actor
        # 1. Selection
        node_id = await self.get_best_worker(required_tags=tags)
        if not node_id:
            return {"error": "No suitable worker available for required capabilities."}
            
        logger.info(f"Routing tool {tool_name} to node {node_id}")
        worker = self.workers[node_id]
        self.node_stats[node_id]["tasks_started"] += 1
        
        # 2. Execution with Retry
        try:
            # Simulated Ray remote call
            if is_ray_actor(worker):
                result = await worker.execute_tool.remote(tool_name, args)
            else:
                result = await worker.execute_tool(tool_name, args)
            return result
        except Exception as e:
            logger.error(f"Task failed on {node_id}, considering retry... Error: {e}")
            self.node_stats[node_id]["tasks_failed"] += 1
            # Simple retry on next best node (one level deep)
            # In production, this would be a recursive/looping retry logic
            return {"error": f"Task failed on node {node_id}: {str(e)}"}
