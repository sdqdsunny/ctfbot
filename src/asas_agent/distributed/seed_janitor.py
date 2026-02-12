import logging
import asyncio
import hashlib
from typing import List, Dict, Any, Set
from .router import SwarmRouter

logger = logging.getLogger(__name__)

class SeedJanitor:
    """
    Global Seed Janitor for distributed Fuzzing.
    Handles deduplication and synchronization of seeds across the swarm.
    """
    def __init__(self, router: SwarmRouter):
        self.router = router
        self.global_seed_pool: Dict[str, Dict[str, Any]] = {} # hash -> seed_data
        self.active_fuzzers: Dict[str, str] = {} # node_id -> container_id
        self.loop_task: Optional[asyncio.Task] = None

    def register_fuzzer(self, node_id: str, container_id: str):
        self.active_fuzzers[node_id] = container_id
        logger.info(f"Fuzzer container {container_id} on {node_id} registered for sync.")

    async def start_sync_loop(self, interval_sec: int = 60):
        """Start the background synchronization loop."""
        if self.loop_task:
            return
        self.loop_task = asyncio.create_task(self._sync_loop(interval_sec))
        logger.info(f"Seed synchronization loop started (Interval: {interval_sec}s)")

    async def stop_sync_loop(self):
        if self.loop_task:
            self.loop_task.cancel()
            self.loop_task = None
            logger.info("Seed synchronization loop stopped.")

    async def _sync_loop(self, interval: int):
        while True:
            try:
                await self.perform_global_sync()
            except Exception as e:
                logger.error(f"Error during global seed sync: {e}")
            await asyncio.sleep(interval)

    async def perform_global_sync(self):
        """
        1. Fetch all new seeds from all workers.
        2. Deduplicate.
        3. Inject missing seeds back to workers.
        """
        if not self.active_fuzzers:
            return

        new_seeds_count = 0
        all_node_seeds: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Fetch
        from .utils import is_ray_actor
        for node_id, container_id in self.active_fuzzers.items():
            worker = self.router.workers.get(node_id)
            if not worker: continue
            
            try:
                # remote call - more robust check for Ray Actor
                if is_ray_actor(worker):
                    seeds = await worker.fetch_seeds.remote(container_id)
                else:
                    seeds = await worker.fetch_seeds(container_id)
                
                all_node_seeds[node_id] = seeds
                
                for seed in seeds:
                    s_hash = hashlib.md5(seed["content_b64"].encode()).hexdigest()
                    if s_hash not in self.global_seed_pool:
                        self.global_seed_pool[s_hash] = seed
                        new_seeds_count += 1
            except Exception as e:
                logger.error(f"Failed to fetch seeds from {node_id}: {e}")

        if new_seeds_count > 0:
            logger.info(f"Sync complete: Found {new_seeds_count} new unique seeds. Total pool: {len(self.global_seed_pool)}")
            
        # 2. Distribute (Injection) - Always check if nodes are missing seeds from the global pool
        # This ensures breakthrough seeds or late-joining nodes get synced.
        for node_id, container_id in self.active_fuzzers.items():
            worker = self.router.workers.get(node_id)
            if not worker: continue
            
            # Identify missing seeds for this node
            # Node's current seeds were collected during the Fetch phase above
            existing_hashes = {hashlib.md5(s["content_b64"].encode()).hexdigest() for s in all_node_seeds.get(node_id, [])}
            missing_seeds = [s for h, s in self.global_seed_pool.items() if h not in existing_hashes]
            
            if missing_seeds:
                try:
                    if is_ray_actor(worker):
                        await worker.inject_seeds.remote(container_id, missing_seeds)
                    else:
                        await worker.inject_seeds(container_id, missing_seeds)
                    logger.debug(f"Injected {len(missing_seeds)} missing seeds into {node_id}")
                except Exception as e:
                    logger.error(f"Failed to inject seeds to {node_id}: {e}")
        
        if new_seeds_count == 0:
            logger.debug("No new seeds found across the swarm.")

    def get_corpus_stats(self) -> Dict[str, Any]:
        return {
            "total_unique_seeds": len(self.global_seed_pool),
            "active_nodes": list(self.active_fuzzers.keys())
        }
