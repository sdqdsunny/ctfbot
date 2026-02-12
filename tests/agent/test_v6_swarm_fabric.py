import pytest
import asyncio
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.router import SwarmRouter
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_swarm_router_intelligent_routing():
    """验证 SwarmRouter 的智能路由逻辑：信誉 + 负载"""
    router = SwarmRouter()
    
    # 模拟两个节点
    node_a = SwarmWorker("Worker-A")
    node_b = SwarmWorker("Worker-B")
    
    # 使用 AsyncMock 模拟异步状态获取
    node_b.get_status = AsyncMock(return_value={
        "node_id": "Worker-B",
        "capabilities": {"gpu": True, "software": {"ida": True}},
        "load": 95, 
        "success_rate": 1.0
    })
    
    node_a.get_status = AsyncMock(return_value={
        "node_id": "Worker-A",
        "capabilities": {"gpu": True, "software": {"ida": True}},
        "load": 10,
        "success_rate": 1.0
    })
    
    router.add_worker("Worker-A", node_a)
    router.add_worker("Worker-B", node_b)
    
    best_node = await router.get_best_worker(required_tags=["gpu"])
    assert best_node == "Worker-A"
    print(f"\n✅ 智能负载均衡验证成功: 任务路由至最优节点 {best_node}")

@pytest.mark.asyncio
async def test_swarm_router_blacklist():
    """验证管理员拉黑功能"""
    router = SwarmRouter()
    node_a = SwarmWorker("Worker-A")
    # Mock status to avoid real calls
    node_a.get_status = AsyncMock(return_value={"node_id": "Worker-A", "load": 0, "capabilities": {}})
    router.add_worker("Worker-A", node_a)
    
    router.ban_node("Worker-A")
    best_node = await router.get_best_worker()
    assert best_node is None
    print(f"\n✅ 管理员拉黑功能验证成功: 被拉黑节点不再参与路由")

@pytest.mark.asyncio
async def test_swarm_router_software_aware():
    """验证软件栈感知逻辑"""
    router = SwarmRouter()
    node_ida = SwarmWorker("IDA-Node")
    node_generic = SwarmWorker("Generic-Node")
    
    node_ida.get_status = AsyncMock(return_value={
        "node_id": "IDA-Node",
        "capabilities": {"software": {"ida": True}},
        "load": 0, "success_rate": 1.0
    })
    
    node_generic.get_status = AsyncMock(return_value={
        "node_id": "Generic-Node",
        "capabilities": {"software": {"ida": False}},
        "load": 0, "success_rate": 1.0
    })
    
    router.add_worker("IDA-Node", node_ida)
    router.add_worker("Generic-Node", node_generic)
    
    best_node = await router.get_best_worker(required_tags=["ida"])
    assert best_node == "IDA-Node"
    print(f"\n✅ 软件栈感知验证成功: 成功匹配具备 IDA 能力的节点")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
