"""reflection prompt 分场景生成测试"""
import pytest
from src.asas_agent.graph.verifier import build_reflection_prompt


class TestReflectionPrompts:

    def test_error_scenario_prompt(self):
        """错误场景 → prompt 包含重试次数和错误信息"""
        prompt = build_reflection_prompt(
            retry_count=0,
            content="sqlmap: connection timed out",
            scenario="error"
        )
        assert "第 1/3 次尝试" in prompt
        assert "connection timed out" in prompt
        assert "检查参数" in prompt

    def test_progress_scenario_prompt(self):
        """有进展但无 flag → prompt 要求继续深入"""
        prompt = build_reflection_prompt(
            retry_count=0,
            content="Found 3 databases: information_schema, mysql, ctf_challenge",
            scenario="progress"
        )
        assert "继续" in prompt or "下一步" in prompt

    def test_stale_scenario_prompt(self):
        """多次成功但无 flag → prompt 建议 PoC 验证"""
        prompt = build_reflection_prompt(
            retry_count=2,
            content="Dumped table: users (admin, password123)",
            scenario="stale"
        )
        assert "PoC" in prompt or "sandbox" in prompt.lower()

    def test_retry_count_increments(self):
        """重试次数正确递增"""
        prompt = build_reflection_prompt(retry_count=1, content="error", scenario="error")
        assert "第 2/3 次尝试" in prompt

    def test_content_truncation(self):
        """过长内容应被截断（不超过 500 字符）"""
        long_content = "A" * 1000
        prompt = build_reflection_prompt(retry_count=0, content=long_content, scenario="error")
        # prompt 中嵌入的内容应截断到 500 字符
        assert "A" * 500 in prompt
        assert "A" * 501 not in prompt

    def test_fallback_scenario(self):
        """未知场景 → 兜底 prompt"""
        prompt = build_reflection_prompt(retry_count=0, content="some output", scenario="unknown")
        assert "第 1/3 次尝试" in prompt
