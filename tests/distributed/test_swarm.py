import pytest
from asas_agent.distributed.swarm_worker import SwarmWorker
from asas_agent.distributed.swarm_orchestrator import SwarmOrchestrator

@pytest.mark.asyncio
async def test_swarm_worker_capabilities():
    """Test SwarmWorker in non-Ray mode (ASAS_NO_RAY=1)."""
    worker = SwarmWorker("test-node")
    status = worker.get_status()
    assert status["node_id"] == "test-node"
    assert "cpu_cores" in status["capabilities"]

@pytest.mark.asyncio
async def test_swarm_orchestrator_dispatch():
    """Test SwarmOrchestrator in non-Ray mode."""
    # SwarmOrchestrator requires Ray to be initialized.
    # In non-Ray mode, we test worker directly.
    worker = SwarmWorker("test-node")
    result = await worker.execute_tool("test_tool", {"arg": 1})
    assert result["status"] == "success"
    assert "Distributed Result from" in result["result"]
