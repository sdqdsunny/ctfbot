import logging
import asyncio
import time
from typing import Dict, List, Optional
from .router import SwarmRouter
from .gpu_job import CrackJob

logger = logging.getLogger(__name__)

class GPUJobManager:
    """
    Orchestrates distributed GPU cracking jobs.
    Handles scheduling, preemption, and failover/resume.
    """
    def __init__(self, router: SwarmRouter):
        self.router = router
        self.pending_queue: List[CrackJob] = [] # High priority first
        self.active_jobs: Dict[str, CrackJob] = {} # job_id -> Job
        self.worker_job_map: Dict[str, str] = {} # worker_id -> job_id
        
        self.scheduler_task: Optional[asyncio.Task] = None
        
    async def submit_job(self, hash_value: str, hash_type: str = "0", wordlist: str = "rockyou.txt", priority: int = 10) -> str:
        """Submit a new cracking job."""
        job = CrackJob(
            hash_value=hash_value,
            hash_type=hash_type,
            wordlist=wordlist,
            priority=priority
        )
        self.pending_queue.append(job)
        # Sort queue by priority desc, then created_at asc
        self.pending_queue.sort(key=lambda x: (-x.priority, x.created_at))
        logger.info(f"Submitted GPU Crack Job {job.job_id} (Hash: {hash_value[:8]}..., Prio: {priority})")
        
        # Trigger scheduler immediately
        if self.scheduler_task and not self.scheduler_task.done():
            self.scheduler_task.cancel() # Debounce/Restart
        self.scheduler_task = asyncio.create_task(self._schedule_loop())
        
        return job.job_id

    async def _schedule_loop(self):
        """Main scheduling loop. Tries to assign pending jobs to free GPU workers."""
        try:
            while self.pending_queue:
                # 1. Find the highest priority pending job
                job = self.pending_queue[0]
                
                # 2. Look for an available GPU worker (idle)
                # First, check for truly idle nodes
                best_node = await self._find_idle_gpu_node()
                
                if best_node:
                    # Assign immediately
                    self.pending_queue.pop(0)
                    await self._assign_job(job, best_node)
                    continue
                
                # 3. If no idle node, check for preemption opportunities
                # Can we preempt a lower priority job running on a GPU node?
                preempt_victim = await self._find_preemptible_node(job.priority)
                if preempt_victim:
                    victim_node, victim_job_id = preempt_victim
                    logger.warning(f"Preempting Job {victim_job_id} on {victim_node} for higher priority Job {job.job_id}")
                    await self._suspend_job(victim_job_id, victim_node)
                    
                    self.pending_queue.pop(0)
                    await self._assign_job(job, victim_node)
                    continue
                
                # No resources available, wait and retry later
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")

    async def _find_idle_gpu_node(self) -> Optional[str]:
        """Find a GPU node that is currently not running any CrackJob."""
        # Get all GPU nodes from router
        # This is a bit inefficient for prototype, but works
        # In real Ray, we'd query actor tags/resources
        all_workers = self.router.workers.keys()
        
        for node_id in all_workers:
            # Check if this node is already busy with a job managed by US
            if node_id in self.worker_job_map:
                continue
            
            # Verify it actually has a GPU (via Router cache or status)
            # We assume router keeps capabilities updated or we check cache
            worker = self.router.workers[node_id]
            try:
                from .utils import is_ray_actor
                if is_ray_actor(worker):
                    status = await worker.get_status.remote()
                else:
                    status = await worker.get_status()
                    if asyncio.iscoroutine(status): status = await status
                
                if status["capabilities"].get("gpu"):
                    return node_id
            except Exception:
                continue
        return None

    async def _find_preemptible_node(self, required_priority: int) -> Optional[tuple]:
        """Find a node running a lower priority job."""
        for node_id, job_id in self.worker_job_map.items():
            current_job = self.active_jobs.get(job_id)
            if current_job and current_job.priority < required_priority:
                return (node_id, job_id)
        return None

    async def _assign_job(self, job: CrackJob, node_id: str):
        """Dispatch job execution to worker."""
        job.status = "RUNNING"
        job.assigned_worker_id = node_id
        job.started_at = time.time()
        
        self.active_jobs[job.job_id] = job
        self.worker_job_map[node_id] = job.job_id
        
        logger.info(f"Assigning Job {job.job_id} to {node_id}")
        
        try:
            worker = self.router.workers[node_id]
            # Call remote start_crack_job
            # Checkpoint handling: if job has checkpoint, we pass it
            args = {
                "job_id": job.job_id,
                "hash": job.hash_value,
                "hash_type": job.hash_type,
                "wordlist": job.wordlist,
                "checkpoint": job.checkpoint_data
            }
            
            from .utils import is_ray_actor
            if is_ray_actor(worker):
                # Fire and forget (async start), we'll poll status later via heartbeat
                # or use a callback mechanism
                # For prototype, we simulate a blocking call to get initial "Started" ack
                await worker.start_crack_job.remote(args)
            else:
                await worker.start_crack_job(args)
                
        except Exception as e:
            logger.error(f"Failed to start job on {node_id}: {e}")
            # Re-queue job
            self._handle_job_failure(job)

    async def _suspend_job(self, job_id: str, node_id: str):
        """Suspend a running job and save its checkpoint."""
        job = self.active_jobs.get(job_id)
        if not job: return
        
        try:
            worker = self.router.workers.get(node_id)
            if worker:
                from .utils import is_ray_actor
                # Call remote pause
                if is_ray_actor(worker):
                    checkpoint = await worker.pause_crack_job.remote(job_id)
                else:
                    checkpoint = await worker.pause_crack_job(job_id)
                
                job.checkpoint_data = checkpoint
                job.progress_percent = 0 # Approximate, or parse from checkpoint metadata
                
            job.status = "PAUSED"
            job.assigned_worker_id = None
            del self.worker_job_map[node_id]
            
            # Put back in pending queue
            self.pending_queue.append(job)
            self.pending_queue.sort(key=lambda x: (-x.priority, x.created_at))
            logger.info(f"Job {job_id} suspended and re-queued with checkpoint.")
            
        except Exception as e:
            logger.error(f"Failed to suspend job {job_id}: {e}")
            # If we utilize checkpointing, even if pause fails (e.g. node crash), 
            # we might still have the last heartbeat checkpoint.
            # For now, force remove mapping
            if node_id in self.worker_job_map:
                del self.worker_job_map[node_id]
            job.status = "PAUSED" # Effectively failed/paused
            self.pending_queue.append(job)

    def _handle_job_failure(self, job: CrackJob):
        """Handle job assignment failure (e.g. immediate crash)."""
        job.status = "PENDING"
        job.assigned_worker_id = None
        if job.job_id in self.active_jobs:
            del self.active_jobs[job.job_id] # Move back to pending
        
        self.pending_queue.append(job)
        if job.assigned_worker_id in self.worker_job_map:
            del self.worker_job_map[job.assigned_worker_id]
