import asyncio

import pytest

from asas_mcp.server import create_app, mcp_server


def test_server_creation():
    app = create_app()
    assert app is not None


def _registered_tool_names() -> set[str]:
    """FastMCP 上真正注册的工具名（权威来源）。"""
    tools = asyncio.run(mcp_server.list_tools())
    return {t.name for t in tools}


def _advertised_tool_names() -> set[str]:
    """HTTP `/tools` 端点对外宣称的工具名。"""
    app = create_app()
    for route in app.routes:
        if getattr(route, "path", None) == "/tools":
            return set(route.endpoint()["tools"])
    raise AssertionError("create_app() 里找不到 /tools 路由")


def test_http_tool_list_matches_mcp_registry():
    """`/tools` 是给 HTTP 调用方的工具目录，不能与 MCP 实际注册的集合漂移。

    它曾少列 5 个工具（ghidra_list_functions / ghidra_decompile_function /
    open_vm_vnc / memory_add / memory_query）——按这份目录写集成的调用方会发现
    "文档里没有但实际能调"的工具，属于典型的文档漂移。
    两处都手写清单，所以这里把它们钉在一起。
    """
    registered = _registered_tool_names()
    advertised = _advertised_tool_names()

    assert registered, "没有从 FastMCP 读到任何工具 —— 注册方式可能变了"

    missing = sorted(registered - advertised)
    extra = sorted(advertised - registered)

    assert not missing, f"/tools 漏列了已注册的工具: {missing}"
    assert not extra, f"/tools 列出了并未注册的工具: {extra}"
