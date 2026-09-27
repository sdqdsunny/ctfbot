"""FlagExtractor 单元测试 — 多格式 CTF flag 正则提取"""
import pytest
from src.asas_agent.graph.verifier import FlagExtractor


class TestFlagExtractor:
    def setup_method(self):
        self.extractor = FlagExtractor()

    def test_extract_standard_flag(self):
        """标准 flag{...} 格式"""
        text = "The answer is flag{hello_world_123}"
        flags = self.extractor.extract(text)
        assert flags == ["flag{hello_world_123}"]

    def test_extract_case_insensitive(self):
        """大小写不敏感: FLAG{} / Flag{}"""
        text = "Found FLAG{UPPER_CASE} and also Flag{Mixed_Case}"
        flags = self.extractor.extract(text)
        assert len(flags) == 2
        assert "FLAG{UPPER_CASE}" in flags
        assert "Flag{Mixed_Case}" in flags

    def test_extract_ctf_prefix(self):
        """CTF{} / ctfshow{} 等非标准前缀"""
        text = "Got CTF{some_value} and ctfshow{another_one}"
        flags = self.extractor.extract(text)
        assert len(flags) == 2

    def test_extract_multiple_flags(self):
        """同一文本中多个 flag"""
        text = "flag{first} some noise flag{second} more noise"
        flags = self.extractor.extract(text)
        assert flags == ["flag{first}", "flag{second}"]

    def test_no_flag_in_text(self):
        """无 flag 时返回空列表"""
        text = "This is just normal text without any flags"
        flags = self.extractor.extract(text)
        assert flags == []

    def test_extract_flag_with_special_chars(self):
        """flag 内含特殊字符: 连字符、下划线、数字"""
        text = "flag{this-is_a-t3st_fl4g-2024}"
        flags = self.extractor.extract(text)
        assert flags == ["flag{this-is_a-t3st_fl4g-2024}"]

    def test_nested_braces_not_greedy(self):
        """不贪婪匹配，遇到第一个 } 就停止"""
        text = "flag{a} other flag{b}"
        flags = self.extractor.extract(text)
        assert flags == ["flag{a}", "flag{b}"]

    def test_deduplication(self):
        """重复 flag 自动去重"""
        text = "flag{dup} and again flag{dup}"
        flags = self.extractor.extract(text)
        assert flags == ["flag{dup}"]

    def test_has_flag_convenience(self):
        """has_flag() 便捷方法"""
        assert self.extractor.has_flag("some flag{ok} here") is True
        assert self.extractor.has_flag("nothing here") is False
