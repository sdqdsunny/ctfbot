import pytest
import ray
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.swarm_orchestrator import SwarmOrchestrator

@pytest.fixture(scope="module")
def ray_fix():
    # Start ray in local mode for testing
    ray.init(local_mode=True, ignore_reinit_error=True)
    yield
    ray.shutdown()

@pytest.mark.asyncio
async def test_swarm_worker_capabilities(ray_fix):
    worker = SwarmWorker.remote("test-node")
    status = await worker.get_status.remote()
    assert status["node_id"] == "test-node"
    assert "cpu_cores" in status["capabilities"]

@pytest.mark.asyncio
async def test_swarm_orchestrator_dispatch(ray_fix):
    orch = SwarmOrchestrator()
    count = orch.discover_workers()
    assert count > 0
    
    result = await orch.dispatch_to_best_worker("test_tool", {"arg": 1})
    assert "Result from worker" in result
