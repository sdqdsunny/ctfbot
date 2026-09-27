"""版本号一致性测试。

原先这里只断言 ``__version__ == "1.0.0"``——一个写死的字面量，而仓库里
另外 8 处声明的版本号各不相同（pyproject 0.6.0 / README 徽章 0.7.0 /
UI 0.1.0 ...）。这种断言恰好看不出真正的问题：它只保证"这一处没被改过"，
对"各处互不相同"完全无感。

现在改为：以 pyproject.toml 为权威，断言所有声明点都与它一致。
权威值与声明点清单都在 ``scripts/check_version.py`` 里，CI 用的是同一个脚本，
避免本地和 CI 各有一套判断标准。

跑法（需要 PYTHONPATH=src，本项目未装 editable 包）::

    PYTHONPATH=src .venv/bin/python -m pytest tests/test_version.py -v
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from check_version import collect  # noqa: E402  （需先补 sys.path）


def test_all_declared_versions_agree():
    """所有声明点的版本号必须一致，不一致就把每一处的值列出来。"""
    found = collect()
    canonical = found["pyproject.toml"]

    mismatched = {name: ver for name, ver in found.items() if ver != canonical}
    assert not mismatched, (
        f"版本号不一致，权威值（pyproject.toml）为 {canonical}，"
        f"以下声明点不同：{mismatched}\n"
        f"  改完可用 python scripts/check_version.py 复查。"
    )


def test_package_versions_match_each_other():
    """两个包各自导出的 __version__ 也必须一致。

    单独拎出来测，是因为这两个值会出现在运行时（/health、MCP 根路由），
    与只在构建期起作用的 pyproject 不同——漂移了会直接对外报错版本。
    """
    from asas_agent import __version__ as agent_version
    from asas_mcp import __version__ as mcp_version

    assert agent_version == mcp_version, (
        f"asas_agent={agent_version} 与 asas_mcp={mcp_version} 不一致"
    )


def test_version_is_not_placeholder():
    """挡住把版本号"占位化"的改动——空串或明显的占位值。"""
    from asas_agent import __version__

    assert __version__.strip(), "版本号不能为空"
    assert __version__.lower() not in {"x", "x.y.z", "0.0.0", "todo"}, (
        f"版本号仍是占位值: {__version__!r}"
    )
    assert __version__[0].isdigit(), f"版本号应以数字开头: {__version__!r}"


@pytest.mark.parametrize("name", ["pyproject.toml"])
def test_canonical_source_is_readable(name):
    """权威来源必须可读——读不到时 check_version 返回 '<读取失败: ...>'，
    这里显式挡一道，免得失败信息里只看到"不一致"而看不出是读崩了。"""
    assert not collect()[name].startswith("<"), f"{name} 读取失败"
