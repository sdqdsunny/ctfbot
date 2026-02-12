import pytest
import asyncio
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.router import SwarmRouter
from asas_agent.distributed.seed_janitor import SeedJanitor
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_seed_sync_deduplication():
    """验证 SeedJanitor 的去重与分发逻辑"""
    router = SwarmRouter()
    janitor = SeedJanitor(router)
    
    # 模拟 Worker A 和 B
    node_a = MagicMock()
    node_b = MagicMock()
    
    seed_1 = {"filename": "id_001", "content_b64": "YWFh"}
    seed_2 = {"filename": "id_002", "content_b64": "YmJi"}
    
    # 设置 fetch_seeds 为 AsyncMock
    node_a.fetch_seeds = AsyncMock(return_value=[seed_1])
    node_a.inject_seeds = AsyncMock(return_value=1)
    node_a.get_status = AsyncMock(return_value={"load": 0, "capabilities": {}})
    
    node_b.fetch_seeds = AsyncMock(return_value=[seed_2])
    node_b.inject_seeds = AsyncMock(return_value=1)
    node_b.get_status = AsyncMock(return_value={"load": 0, "capabilities": {}})
    
    router.add_worker("Worker-A", node_a)
    router.add_worker("Worker-B", node_b)
    
    janitor.register_fuzzer("Worker-A", "container_a")
    janitor.register_fuzzer("Worker-B", "container_b")
    
    # 执行同步
    await janitor.perform_global_sync()
    
    # 验证全局池
    assert len(janitor.global_seed_pool) == 2
    
    # 验证交叉授粉
    node_a.inject_seeds.assert_called()
    node_b.inject_seeds.assert_called()
    
    print("\n✅ 分布式种子同步验证成功: 跨节点『交叉授粉』逻辑正确")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
