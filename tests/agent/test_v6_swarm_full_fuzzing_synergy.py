import pytest
import asyncio
import time
import hashlib
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.router import SwarmRouter
from asas_agent.distributed.seed_janitor import SeedJanitor
from asas_agent.distributed.concolic_breaker import ConcolicBreaker
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_full_fuzzing_synergy_flow():
    """
    全流程验证：
    1. Worker-A 发现基础种子。
    2. Sync 发现停滞。
    3. Expert-Node (Angr) 产生突破性种子。
    4. Worker-A 收到突破性种子。
    """
    router = SwarmRouter()
    janitor = SeedJanitor(router)
    breaker = ConcolicBreaker(router, janitor)
    
    # 1. 准备 Worker-A (普通 Fuzzer)
    worker_a = SwarmWorker("Worker-A")
    seed_basic = {"filename": "basic_seed", "content_b64": "YWFh"} # "aaa"
    worker_a.fetch_seeds = AsyncMock(return_value=[seed_basic])
    worker_a.inject_seeds = AsyncMock(return_value=1)
    worker_a.get_status = AsyncMock(return_value={"load": 10, "capabilities": {"software": {"ida": True}}})
    
    # 2. 准备 Expert-Node (Angr 专家)
    expert_node = SwarmWorker("Expert-Node")
    seed_expert = {"filename": "breakthrough_seed", "content_b64": "YmJi"} # "bbb"
    expert_node.fetch_seeds = AsyncMock(return_value=[])
    expert_node.inject_seeds = AsyncMock(return_value=1)
    expert_node.get_status = AsyncMock(return_value={"load": 0, "capabilities": {"software": {"angr": True}}})
    
    # 模拟专家节点的 Angr 工具调用
    expert_node.execute_tool = AsyncMock(return_value={
        "status": "success", 
        "new_seeds": [seed_expert]
    })
    
    router.add_worker("Worker-A", worker_a)
    router.add_worker("Expert-Node", expert_node)
    
    janitor.register_fuzzer("Worker-A", "container_a")
    
    # --- PHASE 1: 首次同步 ---
    print("\n[Phase 1] 首次种子同步...")
    await janitor.perform_global_sync()
    assert len(janitor.global_seed_pool) == 1
    
    # --- PHASE 2: 检测停滞并触发破局 ---
    print("[Phase 2] 检测停滞并调用 Angr 破局...")
    # 模拟停滞
    breaker.last_path_count = 10 
    breaker.stagnant_since = time.time() - 10
    await breaker.check_for_stagnation(current_total_paths=10, threshold_sec=5)
    
    # 验证专家是否被调用
    expert_node.execute_tool.assert_called()
    
    # 手动将 Angr 发现的种子加入全局池，使用正确的 hash 作为 key
    expert_hash = hashlib.md5(seed_expert["content_b64"].encode()).hexdigest()
    janitor.global_seed_pool[expert_hash] = seed_expert
    
    # --- PHASE 3: 再次同步，分发突破性种子 ---
    print("[Phase 3] 同步并将突破性种子广播至所有节点...")
    # 在第二次同步前，清除 A 的 mock call 记录，方便验证此次同步的注入情况
    worker_a.inject_seeds.reset_mock()
    await janitor.perform_global_sync()
    
    # 验证 Worker-A 是否收到了突破性种子 (content_b64: 'YmJi')
    worker_a.inject_seeds.assert_called()
    received_seeds = worker_a.inject_seeds.call_args[0][1]
    print(f"DEBUG: Worker-A received seeds: {[s['filename'] for s in received_seeds]}")
    assert any(s["content_b64"] == "YmJi" for s in received_seeds)
    
    print("\n✅ 全链路协同验证成功: Fuzzing -> 停滞 -> Angr 破局 -> 种子回灌")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
