"""should_continue L1 验证 + flag_capture 节点测试"""
import pytest
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from src.asas_agent.graph.verifier import flag_extractor


class TestShouldContinueL1:
    """测试 L1 flag 格式验证的 FlagExtractor 在 should_continue 场景下的行为"""

    def test_tool_output_contains_flag(self):
        """工具输出包含 flag{...} → FlagExtractor 能提取"""
        tool_content = "Database dump: flag{sqli_success_123}"
        flags = flag_extractor.extract(tool_content)
        assert flags == ["flag{sqli_success_123}"]

    def test_tool_output_error_no_flag(self):
        """工具输出包含 error 但无 flag → 返回空"""
        tool_content = "Error: connection refused"
        flags = flag_extractor.extract(tool_content)
        assert flags == []
        assert flag_extractor.has_flag(tool_content) is False

    def test_tool_output_success_no_flag(self):
        """工具输出成功但无 flag → 返回空"""
        tool_content = "Found 3 open ports: 22, 80, 443"
        flags = flag_extractor.extract(tool_content)
        assert flags == []

    def test_sqlmap_dump_output(self):
        """真实 sqlmap dump 输出"""
        output = """
        Table: secrets
        +----+---------------------------+
        | id | value                     |
        +----+---------------------------+
        | 1  | flag{sql1_un10n_1nj3ct}   |
        +----+---------------------------+
        """
        flags = flag_extractor.extract(output)
        assert flags == ["flag{sql1_un10n_1nj3ct}"]

    def test_has_flag_detects_presence(self):
        """has_flag 快速检测"""
        assert flag_extractor.has_flag("result: flag{abc}") is True
        assert flag_extractor.has_flag("no flag here") is False
        assert flag_extractor.has_flag("CTF{test}") is True
