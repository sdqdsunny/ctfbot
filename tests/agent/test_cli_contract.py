"""CLI 契约测试：退出码 + v2 的工具注册。

这两件事都是"坏得不出声"的类型，所以各自锁一条：

1. **退出码**——改造前无论成功、失败、环境没配好，进程一律以 0 退出，
   脚本/CI 完全无从判断。现在约定了 0/1/2/3（见 ``asas_agent/__main__.py`` 顶部），
   这里断言各码互不相等且关键路径返回正确的码。

2. **v2 的 dispatch_to_agent**——这个工具不是 MCP 工具，得手动补进列表，
   而补的代码原先只写在 v3 里。于是 v2 一决定派发子代理就拿到
   "Tool 'dispatch_to_agent' not found"，任务当场哑火却仍以 0 退出。
   下面用打桩的图把传给 ``create_react_agent_graph`` 的工具列表截下来断言，
   而不是去读源码字符串——后者只能证明"写了"，证明不了"生效了"。

跑法（需要 PYTHONPATH=src，本项目未装 editable 包）::

    PYTHONPATH=src .venv/bin/python -m pytest tests/agent/test_cli_contract.py -v
"""
import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from langchain_core.tools import tool

from asas_agent.__main__ import (
    EXIT_NO_FLAG,
    EXIT_OK,
    EXIT_RUN_ERROR,
    EXIT_STARTUP_ERROR,
    _collect_flags,
    _ensure_dispatch_tool,
    main_cli,
)


@tool
def _some_mcp_tool(x: str) -> str:
    """一个占位的 MCP 工具。"""
    return x


@pytest.fixture(autouse=True)
def _isolate_process_env():
    """清掉并还原 main_cli 写的进程级环境变量。

    main_cli 会设 ASAS_MOCK_MODE（让子代理也走 mock）和 FASTMCP_LOG_LEVEL。
    对真实 CLI 这是对的——进程跑完就结束；但在测试进程里它会一直留着，
    污染后面同进程的其他测试：dispatcher 一旦看到 ASAS_MOCK_MODE=1 就改走
    分支、不再调用 create_llm，于是按"真实逻辑"断言的用例会莫名其妙地挂。

    这里手工快照/还原，而不是用 monkeypatch.delenv——后者对"键本来就不存在"
    的处理在不同 pytest 版本间不一致，而本夹具必须两种情况都稳妥。
    """
    keys = ("ASAS_MOCK_MODE", "FASTMCP_LOG_LEVEL")
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


class _EmptyGraph:
    """不产出任何事件的图，用来把 run_* 的流程空跑到底。"""

    async def astream(self, *args, **kwargs):
        return
        yield  # pragma: no cover  — 让本方法是 async generator


# --------------------------------------------------------------------------
# 退出码
# --------------------------------------------------------------------------

def test_exit_codes_are_distinct():
    """四个码必须互不相同，否则调用方无法区分结果。"""
    codes = [EXIT_OK, EXIT_RUN_ERROR, EXIT_STARTUP_ERROR, EXIT_NO_FLAG]
    assert len(set(codes)) == len(codes)


def test_no_target_is_startup_error():
    """既没给 target 也没给 --url：属于环境/用法问题，退出码 2。"""
    result = CliRunner().invoke(main_cli, ["--v3", "--llm", "mock"])
    assert result.exit_code == EXIT_STARTUP_ERROR


def test_missing_config_is_startup_error(tmp_path):
    """显式指定的配置不存在：退出码 2，而不是静默回退到别的文件。"""
    missing = tmp_path / "nope.yaml"
    result = CliRunner().invoke(
        main_cli, ["probe", "--v3", "--llm", "mock", "--config", str(missing)]
    )
    assert result.exit_code == EXIT_STARTUP_ERROR


def test_run_without_flag_reports_no_flag():
    """跑完但没拿到 flag → 3（与"环境挂了"的 2 区分开）。"""
    with _patched_v2(tools=[_some_mcp_tool]):
        result = CliRunner().invoke(main_cli, ["hello", "--v2", "--llm", "mock"])
    assert result.exit_code == EXIT_NO_FLAG


# --------------------------------------------------------------------------
# dispatch_to_agent 注册
# --------------------------------------------------------------------------

def test_ensure_dispatch_tool_appends_when_missing():
    tools = [_some_mcp_tool]
    _ensure_dispatch_tool(tools)
    assert any(t.name == "dispatch_to_agent" for t in tools)


def test_ensure_dispatch_tool_does_not_duplicate():
    tools: list = []
    _ensure_dispatch_tool(tools)
    _ensure_dispatch_tool(tools)
    names = [t.name for t in tools]
    assert names.count("dispatch_to_agent") == 1


def test_run_v2_binds_dispatch_to_agent():
    """v2 必须拿到 dispatch_to_agent —— 这正是原先漏掉、导致派发即失败的那一步。"""
    captured = []

    with _patched_v2(tools=[_some_mcp_tool], captured=captured):
        CliRunner().invoke(main_cli, ["scan the target", "--v2", "--llm", "mock"])

    assert captured, "create_react_agent_graph 未被调用"
    bound = [t.name for t in captured[0]]
    assert "dispatch_to_agent" in bound, f"v2 未绑定 dispatch_to_agent，实得 {bound}"
    assert "_some_mcp_tool" in bound, "MCP 工具不应被丢掉"


# --------------------------------------------------------------------------
# flag 归集
# --------------------------------------------------------------------------

def test_collect_flags_extracts_and_dedupes():
    acc: list = []
    _collect_flags(acc, "前一段 flag{alpha} 后一段")
    _collect_flags(acc, "重复出现 flag{alpha}，另加 flag{beta}")
    assert acc == ["flag{alpha}", "flag{beta}"]


def test_collect_flags_ignores_noise():
    acc: list = []
    _collect_flags(acc, "没有任何 flag 的普通输出")
    assert acc == []


# --------------------------------------------------------------------------
# 打桩工具
# --------------------------------------------------------------------------

class _patched_v2:
    """把 v2 路径上的外部依赖全部替换掉，只留下"工具怎么被传下去"这件事。"""

    def __init__(self, tools, captured=None):
        self._tools = tools
        self._captured = captured if captured is not None else []

    def __enter__(self):
        captured = self._captured
        tools = self._tools

        async def fake_convert(_client):
            return list(tools)

        def fake_graph(llm, tools_arg, *a, **kw):
            captured.append(list(tools_arg))
            return _EmptyGraph()

        # run_v2 在函数内 import，因此 patch 其来源模块的属性即可
        self._patches = [
            patch(
                "asas_agent.mcp_client.client.MCPToolClient",
                lambda *a, **kw: object(),
            ),
            patch(
                "asas_agent.llm.tool_adapter.convert_mcp_to_langchain_tools",
                fake_convert,
            ),
            patch("asas_agent.graph.workflow.create_react_agent_graph", fake_graph),
            # 不依赖本地 v3_config.yaml（它被 gitignore，干净环境里没有）。
            # config_loader 是单例，patch 它的方法即可覆盖 run_v2 里的那次取用。
            patch(
                "asas_agent.utils.config.config_loader.load_config",
                lambda *a, **kw: {"orchestrator": {"provider": "mock"}},
            ),
        ]
        for p in self._patches:
            p.start()
        return captured

    def __exit__(self, *exc):
        for p in self._patches:
            p.stop()
        return False
