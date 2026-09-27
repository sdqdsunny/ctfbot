"""验证闭环端到端集成测试"""
import pytest
from src.asas_agent.graph.verifier import FlagExtractor, build_reflection_prompt


class TestVerificationE2E:

    def test_l1_flag_from_sqlmap_dump(self):
        """sqlmap dump 输出 → L1 提取"""
        output = """
        Table: secrets
        +----+---------------------------+
        | id | flag                      |
        +----+---------------------------+
        | 1  | flag{sql1_un10n_1nj3ct}   |
        +----+---------------------------+
        """
        assert FlagExtractor().extract(output) == ["flag{sql1_un10n_1nj3ct}"]

    def test_l1_flag_from_crypto(self):
        """Base64 解码输出 → L1 提取"""
        assert FlagExtractor().extract("Decoded: flag{b4s364_d3c0d3d}") == ["flag{b4s364_d3c0d3d}"]

    def test_l1_flag_from_ncat_output(self):
        """netcat 输出中提取 flag"""
        output = "Connection established. Server says: flag{nc_r3v3rs3_sh3ll}"
        assert FlagExtractor().extract(output) == ["flag{nc_r3v3rs3_sh3ll}"]

    def test_l2_error_reflection(self):
        """L2: 错误 → 重试 prompt"""
        prompt = build_reflection_prompt(0, "Error: sqlmap no injection", "error")
        assert "第 1/3 次尝试" in prompt
        assert "检查参数" in prompt

    def test_l2_progress_reflection(self):
        """L2: 有进展 → 深入 prompt"""
        prompt = build_reflection_prompt(0, "Found databases: ctf_db", "progress")
        assert "继续" in prompt or "下一步" in prompt

    def test_l2_stale_reflection(self):
        """L2: 停滞 → PoC prompt"""
        prompt = build_reflection_prompt(2, "Dumped users: admin", "stale")
        assert "PoC" in prompt or "sandbox" in prompt.lower()

    def test_real_ctf_flag_formats(self):
        """真实 CTF 平台 flag 格式"""
        extractor = FlagExtractor()
        cases = [
            ("ctfshow{d2b1f4a3e5c6789}", ["ctfshow{d2b1f4a3e5c6789}"]),
            ("HITCON{y0u_f0und_1t}", ["HITCON{y0u_f0und_1t}"]),
            ("DASCTF{ez_sql}", ["DASCTF{ez_sql}"]),
            ("qwb{strong_net_cup_2024}", ["qwb{strong_net_cup_2024}"]),
            ("moectf{cute_moe_flag}", ["moectf{cute_moe_flag}"]),
        ]
        for text, expected in cases:
            assert extractor.extract(text) == expected, f"Failed: {text}"

    def test_mixed_output_with_noise(self):
        """带噪声的真实输出中提取 flag"""
        output = """
        [*] Starting sqlmap scan...
        [INFO] Testing connection to target URL
        [INFO] GET parameter 'id' is vulnerable
        [*] Fetching data...
        
        Database: challenge_db
        Table: flags
        [1 entry]
        +----+-------------------------------+
        | id | value                         |
        +----+-------------------------------+
        | 1  | flag{un10n_b4s3d_1nj3ct10n}   |
        +----+-------------------------------+
        
        [*] Shutting down...
        """
        extractor = FlagExtractor()
        flags = extractor.extract(output)
        assert len(flags) == 1
        assert flags[0] == "flag{un10n_b4s3d_1nj3ct10n}"

    def test_verification_flow_l1_to_l2(self):
        """验证流程：L1 无 flag → L2 生成 prompt → 包含正确指导"""
        # 模拟：工具返回了有价值的信息但没有 flag
        tool_output = "Found: admin:password123, guest:guest"
        extractor = FlagExtractor()
        
        # L1: 没有 flag
        assert extractor.has_flag(tool_output) is False
        
        # L2: 生成进展分析 prompt
        prompt = build_reflection_prompt(0, tool_output, "progress")
        assert "flag{" in prompt.lower() or "flag" in prompt.lower()
        assert "admin:password123" in prompt
