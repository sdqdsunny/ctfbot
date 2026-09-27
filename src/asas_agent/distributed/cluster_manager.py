try:
    import ray
except ImportError:
    ray = None

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ClusterManager:
    """
    Manages the lifecycle of the Ray cluster for CTF-ASAS.
    Supports either connecting to an existing cluster or starting a local head node.
    """
    def __init__(self, address: Optional[str] = None):
        self.address = address or os.environ.get("RAY_ADDRESS")
        self.is_initialized = False

    def initialize(self) -> bool:
        """Initialize the cluster connection."""
        if not ray:
            logger.error("Ray library is not installed.")
            return False
            
        try:
            if not ray.is_initialized():
                if self.address:
                    logger.info(f"Connecting to existing Ray cluster at {self.address}...")
                    ray.init(address=self.address)
                else:
                    logger.info("Starting local Ray head node...")
                    ray.init()
            
            self.is_initialized = True
            node_info = ray.nodes()
            logger.info(f"Ray initialized successfully. Nodes in cluster: {len(node_info)}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Ray cluster: {e}")
            return False

    def shutdown(self):
        """Shutdown the cluster connection."""
        if ray and ray.is_initialized():
            ray.shutdown()
            self.is_initialized = False
            logger.info("Ray cluster connection shut down.")

    def get_cluster_status(self) -> Dict[str, Any]:
        """Fetch general cluster health and node counts."""
        if not self.is_initialized or not ray:
            return {"status": "Disconnected"}
            
        nodes = ray.nodes()
        active_nodes = [n for n in nodes if n["Alive"]]
        
        return {
            "status": "Connected",
            "total_nodes": len(nodes),
            "active_nodes": len(active_nodes),
            "ray_version": ray.__version__
        }
