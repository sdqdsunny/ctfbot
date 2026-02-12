import pytest
import asyncio
import time
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.router import SwarmRouter
from asas_agent.distributed.seed_janitor import SeedJanitor
from asas_agent.distributed.concolic_breaker import ConcolicBreaker
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_concolic_breaker_trigger():
    """验证当 Fuzzing 停滞时，自动触发 Angr 破局逻辑"""
    router = SwarmRouter()
    janitor = SeedJanitor(router)
    breaker = ConcolicBreaker(router, janitor)
    
    # 模拟专家节点 (具备 Angr 能力)
    expert_node = SwarmWorker("Expert-Node")
    expert_node.get_status = AsyncMock(return_value={
        "load": 0, 
        "capabilities": {"software": {"angr": True}}
    })
    # 模拟执行 Angr 工具
    expert_node.execute_tool = AsyncMock(return_value={
        "status": "success", 
        "new_seeds": [{"filename": "breakthrough_1", "content_b64": "Y2Nj"}]
    })
    
    router.add_worker("Expert-Node", expert_node)
    
    # 注入一个初始种子
    janitor.global_seed_pool["hash1"] = {"filename": "seed1", "content_b64": "YWFh"}
    
    # 模拟停滞情况：10 条路径，5 秒阈值（测试用）
    breaker.last_path_count = 10
    breaker.stagnant_since = time.time() - 10 # 已经停滞了 10 秒
    
    # 执行检查 (阈值设为 5 秒)
    await breaker.check_for_stagnation(current_total_paths=10, threshold_sec=5)
    
    # 验证是否输出了 Angr 任务
    expert_node.execute_tool.assert_called()
    args = expert_node.execute_tool.call_args[0][1]
    assert args["strategy"] == "explore_new_branches"
    
    print("\n✅ Concolic 破局触发验证成功: 停滞检测与专家节点调度工作正常")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
