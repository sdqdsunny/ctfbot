"""Tests for CTF script registry."""
import pytest
from src.asas_mcp.memory.script_registry import ScriptRegistry


@pytest.fixture
def registry(tmp_path):
    """创建带测试脚本目录的注册表"""
    (tmp_path / "RSA综合脚本利用").mkdir()
    (tmp_path / "RSA综合脚本利用" / "rsa_attack.py").write_text("# RSA attack")

    (tmp_path / "CRC32校验爆破").mkdir()
    crc_sub = tmp_path / "CRC32校验爆破" / "crc32"
    crc_sub.mkdir()
    (crc_sub / "crc32.py").write_text("# CRC32")

    (tmp_path / "usb流量").mkdir()
    (tmp_path / "usb流量" / "keyboard.py").write_text("# USB keyboard")

    (tmp_path / "双参数爆破脚本").mkdir()
    (tmp_path / "双参数爆破脚本" / "brust.py").write_text("# brute")

    (tmp_path / "steghide爆破密码").mkdir()
    (tmp_path / "steghide爆破密码" / "steghide_brute.py").write_text("# steghide")

    return ScriptRegistry(str(tmp_path))


class TestListScripts:
    def test_list_all(self, registry):
        scripts = registry.list_scripts()
        assert len(scripts) >= 5

    def test_list_by_crypto(self, registry):
        scripts = registry.list_scripts(category="crypto")
        names = [s["name"] for s in scripts]
        assert any("RSA" in n for n in names)

    def test_list_by_traffic(self, registry):
        scripts = registry.list_scripts(category="traffic")
        names = [s["name"] for s in scripts]
        assert any("usb" in n.lower() for n in names)

    def test_list_by_web(self, registry):
        scripts = registry.list_scripts(category="web")
        names = [s["name"] for s in scripts]
        assert any("爆破" in n for n in names)

    def test_list_by_stego(self, registry):
        scripts = registry.list_scripts(category="stego")
        names = [s["name"] for s in scripts]
        assert any("steghide" in n.lower() for n in names)

    def test_list_nonexistent_category(self, registry):
        scripts = registry.list_scripts(category="blockchain")
        assert scripts == []

    def test_sorted_by_name(self, registry):
        scripts = registry.list_scripts()
        names = [s["name"] for s in scripts]
        assert names == sorted(names)


class TestFindScript:
    def test_find_rsa(self, registry):
        result = registry.find_script("RSA")
        assert result is not None
        assert result["path"].endswith(".py")
        assert result["category"] == "crypto"

    def test_find_usb(self, registry):
        result = registry.find_script("usb")
        assert result is not None
        assert result["category"] == "traffic"

    def test_find_nonexistent(self, registry):
        result = registry.find_script("不存在的工具xyz")
        assert result is None

    def test_find_case_insensitive(self, registry):
        result = registry.find_script("rsa")
        assert result is not None


class TestCategorize:
    def test_categorize_crypto(self, registry):
        assert registry._categorize("RSA综合脚本利用") == "crypto"

    def test_categorize_traffic(self, registry):
        assert registry._categorize("usb流量") == "traffic"

    def test_categorize_unknown(self, registry):
        assert registry._categorize("未知工具") == "misc"


class TestEdgeCases:
    def test_empty_dir(self, tmp_path):
        registry = ScriptRegistry(str(tmp_path / "nonexistent"))
        assert registry.list_scripts() == []

    def test_script_count(self, registry):
        scripts = registry.list_scripts()
        crc = next((s for s in scripts if "CRC32" in s["name"]), None)
        assert crc is not None
        assert crc["script_count"] >= 1
