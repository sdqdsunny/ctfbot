import pytest
import asyncio
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.router import SwarmRouter
from asas_agent.distributed.gpu_manager import GPUJobManager
from asas_agent.distributed.gpu_job import CrackJob
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_gpu_fault_tolerance():
    """验证 Worker 故障场景下的任务恢复"""
    router = SwarmRouter()
    manager = GPUJobManager(router)
    
    async def schedule_once(self):
        try:
             # Find best Idle
             if self.pending_queue:
                job = self.pending_queue[0]
                best_node = await self._find_idle_gpu_node()
                if best_node:
                    self.pending_queue.pop(0)
                    await self._assign_job(job, best_node)
        except Exception as e:
            pass

    import types
    manager._schedule_loop_one_pass = types.MethodType(schedule_once, manager)

    # 1. 模拟一个 GPU 节点 GPU-A (不稳定)
    node_a = SwarmWorker("GPU-A")
    node_a.get_status = AsyncMock(return_value={"load": 20, "capabilities": {"gpu": True}})
    
    # 定义 node_a 的 behavior: 启动任务时抛出异常 (模拟崩溃)
    node_a.start_crack_job = AsyncMock(side_effect=Exception("Connection Reset by Peer (Simulated Crash)"))
    
    router.add_worker("GPU-A", node_a)
    
    # 2. 模拟另一个 GPU 节点 GPU-B (稳定备用)
    node_b = SwarmWorker("GPU-B")
    node_b.get_status = AsyncMock(return_value={"load": 10, "capabilities": {"gpu": True}})
    node_b.start_crack_job = AsyncMock(return_value=True)
    
    router.add_worker("GPU-B", node_b)
    
    # [场景] 提交一个高优先级任务
    job = await manager.submit_job(hash_value="critical_hash", priority=100)
    
    # 第一次调度尝试 (Manager 会找到空闲的 GPU-A 并尝试分配)
    # 由于 GPU-A 是按顺序遍历到的第一个空闲GPU
    # 我们先让 GPU-B "假装忙" 以迫使分配给 A，或者确保 A 排在前面
    # 简单起见，find_idle_gpu_node 返回 keys 的顺序是不确定的，这里我们 mock 一下 find_idle
    
    # Mock find_idle_gpu_node 首次返回 'GPU-A'
    original_find = manager._find_idle_gpu_node
    manager._find_idle_gpu_node = AsyncMock(side_effect=["GPU-A", "GPU-B"])
    
    print("\n[Step 1] Attempting to schedule on GPU-A (Faulty Node)...")
    await manager._schedule_loop_one_pass()
    
    # 调度器应该调用了 assign_job -> node_a.start_crack_job -> 抛出异常
    # 验证 Job 状态是否处于 PENDING (即失败后回退)
    job_obj = manager.active_jobs.get(job)
    if job_obj is None: # 如果从 active 移除了，则在 pending 中
        job_obj = [j for j in manager.pending_queue if j.job_id == job][0]
        
    assert job_obj.status == "PENDING"
    assert job_obj.assigned_worker_id is None
    print("✅ 故障检测成功：任务未卡在死节点，已回退至 Pending 队列")
    
    # [Step 2] 第二次调度尝试 (Manager 应该找到 GPU-B)
    print("[Step 2] Attempting to reschedule on GPU-B (Backup Node)...")
    await manager._schedule_loop_one_pass()
    
    current_job = manager.active_jobs[job]
    assert current_job.status == "RUNNING"
    assert current_job.assigned_worker_id == "GPU-B"
    print("✅ 故障恢复成功：任务已漂移至备用节点执行")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
