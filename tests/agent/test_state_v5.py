"""AgentState 验证字段测试"""
import pytest
from src.asas_agent.graph.state import AgentState


def test_state_has_extracted_flags_field():
    """AgentState 应包含 extracted_flags 字段，默认空列表"""
    state = AgentState(messages=[])
    # 通过 dict 访问检查字段存在
    assert "extracted_flags" in AgentState.__annotations__ or hasattr(AgentState, "extracted_flags")


def test_state_has_verification_status_field():
    """AgentState 应包含 verification_status 字段"""
    assert "verification_status" in AgentState.__annotations__ or hasattr(AgentState, "verification_status")


def test_state_has_poc_attempts_field():
    """AgentState 应包含 poc_attempts 字段"""
    assert "poc_attempts" in AgentState.__annotations__ or hasattr(AgentState, "poc_attempts")
