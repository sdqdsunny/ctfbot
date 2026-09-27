import pytest
import asyncio
import time
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.router import SwarmRouter
from asas_agent.distributed.gpu_manager import GPUJobManager
from asas_agent.distributed.gpu_job import CrackJob
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_gpu_manager_preemption():
    """验证 GPU 任务管理器的优先级抢占逻辑"""
    router = SwarmRouter()
    manager = GPUJobManager(router)
    
    # 修改 _schedule_loop 以支持单步调试（避免无限循环）
    async def schedule_once(self):
        try:
            # 执行一次完整的调度逻辑
            if self.pending_queue:
                job = self.pending_queue[0]
                best_node = await self._find_idle_gpu_node()
                if best_node:
                    self.pending_queue.pop(0)
                    await self._assign_job(job, best_node)
                    return

                preempt_victim = await self._find_preemptible_node(job.priority)
                if preempt_victim:
                    victim_node, victim_job_id = preempt_victim
                    await self._suspend_job(victim_job_id, victim_node)
                    self.pending_queue.pop(0)
                    await self._assign_job(job, victim_node)
                    return
        except Exception as e:
            print(f"Error: {e}")

    # Patch the method
    import types
    manager._schedule_loop_one_pass = types.MethodType(schedule_once, manager)
    
    # 模拟一个 GPU 节点
    node_gpu = SwarmWorker("GPU-Node")
    node_gpu.get_status = AsyncMock(return_value={
        "load": 50, 
        "capabilities": {"gpu": True}
    })
    
    node_gpu.start_crack_job = AsyncMock(return_value=True)
    node_gpu.pause_crack_job = AsyncMock(return_value="fake_checkpoint_data_base64")
    
    router.add_worker("GPU-Node", node_gpu)
    
    # [Step 1] 提交低优先级任务
    print("\n[Step 1] Submitting low priority job...")
    job_low = CrackJob(hash_value="low", priority=1)
    manager.pending_queue.append(job_low)
    
    # 手动触发一次调度
    await manager._schedule_loop_one_pass()
    
    assert manager.worker_job_map.get("GPU-Node") == job_low.job_id
    assert manager.active_jobs[job_low.job_id].status == "RUNNING"
    print("✅ 低优先级任务成功调度至空闲 GPU 节点")
    
    # [Step 2] 提交高优先级任务
    print("[Step 2] Submitting high priority job...")
    job_high = CrackJob(hash_value="high", priority=10)
    manager.pending_queue.append(job_high)
    manager.pending_queue.sort(key=lambda x: (-x.priority, x.created_at))
    
    # 再次触发调度，期望抢占
    await manager._schedule_loop_one_pass()
    
    # 验证抢占
    assert manager.worker_job_map.get("GPU-Node") == job_high.job_id
    assert manager.active_jobs[job_low.job_id].status == "PAUSED"
    assert manager.active_jobs[job_high.job_id].status == "RUNNING"
    print("✅ 高优先级任务成功抢占资源")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
