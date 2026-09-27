"""dispatcher flag 提取统一性测试"""
import pytest
from src.asas_agent.graph.verifier import flag_extractor


class TestDispatcherFlagExtraction:

    def test_extractor_matches_dispatcher_cases(self):
        """FlagExtractor 覆盖 dispatcher 原有的 re.search 逻辑"""
        test_cases = [
            ("flag{hello}", ["flag{hello}"]),
            ("FLAG{UPPER}", ["FLAG{UPPER}"]),
            ("No flag here", []),
            ("CTF{custom_prefix}", ["CTF{custom_prefix}"]),
            ("ctfshow{web1_answer}", ["ctfshow{web1_answer}"]),
        ]
        for text, expected in test_cases:
            result = flag_extractor.extract(text)
            assert result == expected, f"Failed for '{text}': {result} != {expected}"

    def test_extractor_first_flag_as_primary(self):
        """多个 flag 时取第一个作为主 flag（与 dispatcher 行为一致）"""
        text = "Found flag{first} and flag{second}"
        flags = flag_extractor.extract(text)
        assert flags[0] == "flag{first}"

    def test_extractor_handles_long_reasoning(self):
        """长文本中正确提取 flag"""
        long_text = "A" * 5000 + " flag{hidden_deep} " + "B" * 5000
        flags = flag_extractor.extract(long_text)
        assert flags == ["flag{hidden_deep}"]
