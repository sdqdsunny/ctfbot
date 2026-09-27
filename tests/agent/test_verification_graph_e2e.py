"""验证闭环 — 真正走图的端到端集成测试。

与 ``test_verification_e2e.py`` 的区别：那份只直接调用 ``verifier`` 的纯函数
（``FlagExtractor`` / ``build_reflection_prompt``），从不编译或运行 LangGraph。
本文件用脚本化 LLM + 真实工具节点驱动 ``create_orchestrator_graph``，断言三件事：

1. ``should_continue`` 对 ToolMessage 的路由（flag_capture / reflection / orchestrator / END）
2. ``flag_capture_node`` 是否真的把 flag 写进了 state
3. ``reflection_node`` 注入的 HumanMessage 内容与其场景判定（error / progress / stale）

跑法（需要 PYTHONPATH=src，本项目未装 editable 包）::

    PYTHONPATH=src .venv/bin/python -m pytest tests/agent/test_verification_graph_e2e.py -v
"""
from collections import deque
from uuid import uuid4

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from asas_agent.graph.workflow import create_orchestrator_graph


# --------------------------------------------------------------------------
# 测试替身
# --------------------------------------------------------------------------

class ScriptedLLM:
    """按剧本依次返回 AIMessage，并记录每次 invoke 收到的消息。

    剧本耗尽时抛错而非静默返回——一个预期外的循环会因此变成清晰的失败，
    而不是让测试在 END 处安静地通过。
    """

    def __init__(self, script: list[AIMessage]):
        self._script = deque(script)
        self.calls: list[list] = []

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages, **kwargs) -> AIMessage:
        self.calls.append(list(messages))
        if not self._script:
            raise AssertionError(
                f"LLM 剧本已耗尽，但图第 {len(self.calls)} 次调用它 —— 存在预期外的循环"
            )
        return self._script.popleft()

    async def ainvoke(self, messages, **kwargs) -> AIMessage:
        return self.invoke(messages)


def make_fake_tool(name: str, outputs: list[str]):
    """构造一个按顺序吐出 ``outputs`` 的假工具，用于驱动 tools 节点。"""
    pending = deque(outputs)

    @tool(name)
    def _fake(payload: str = "") -> str:
        """Fake CTF tool used by graph integration tests."""
        if not pending:
            raise AssertionError(f"工具 {name} 的输出队列已耗尽")
        return pending.popleft()

    return _fake


def tool_call(name: str, args: dict | None = None) -> AIMessage:
    """构造一条发起工具调用的 AIMessage。"""
    return AIMessage(content="", tool_calls=[{
        "name": name,
        "args": args or {"payload": "target"},
        "id": f"call_{uuid4().hex[:8]}",
        "type": "tool_call",
    }])


@pytest.fixture(autouse=True)
def _block_uplink(monkeypatch):
    """阻断 orchestrator 对 localhost:8765 的 uplink 轮询。

    该轮询的失败会被静默吞掉，但若开发机上 UI 服务正在运行，它会向消息流注入
    HumanMessage，让断言变得不确定。这里强制连接失败以保证测试确定性。
    """
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("uplink disabled in tests")

    monkeypatch.setattr(httpx, "Client", _boom)


async def run_graph(llm, tools, initial_state: dict | None = None) -> dict:
    """编译并运行编排图，返回最终 state。"""
    app = create_orchestrator_graph(llm, tools)
    state = {
        "messages": [HumanMessage(content="solve the challenge")],
        "platform_url": "http://mock.local",
        "platform_token": "tok",
    }
    if initial_state:
        state.update(initial_state)
    return await app.ainvoke(state)


def injected_user_messages(result: dict) -> list[str]:
    """取出图运行期间作为反馈注入的 HumanMessage（排除最初的用户输入）。"""
    return [
        str(m.content)
        for m in result["messages"]
        if isinstance(m, HumanMessage) and m.content != "solve the challenge"
    ]


# --------------------------------------------------------------------------
# 结构：图里确实有验证闭环的接线
# --------------------------------------------------------------------------

def test_graph_contains_verification_nodes():
    """flag_capture / reflection 节点真实存在于编译后的图中。"""
    app = create_orchestrator_graph(ScriptedLLM([]), [])
    nodes = set(app.get_graph().nodes)
    assert {"orchestrator", "tools", "reflection", "flag_capture"} <= nodes


# --------------------------------------------------------------------------
# L1：flag 命中 → flag_capture → END
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_l1_hit_routes_to_flag_capture_and_ends():
    """工具输出含 flag → 路由到 flag_capture，写入 state 后直接终止。"""
    fake = make_fake_tool("fake_dump", ["Table: flags\n| 1 | flag{gr4ph_l1_h1t} |"])
    llm = ScriptedLLM([tool_call("fake_dump")])

    result = await run_graph(llm, [fake])

    assert result["extracted_flags"] == ["flag{gr4ph_l1_h1t}"]
    assert result["verification_status"] == "l1_passed"
    # 命中即终止：orchestrator 不应被再次调用
    assert len(llm.calls) == 1
    assert isinstance(result["messages"][-1], ToolMessage)
    assert injected_user_messages(result) == []


@pytest.mark.asyncio
async def test_l1_hit_collects_multiple_flags_without_duplicates():
    """同一轮工具输出里的多个 flag 都被捕获，且去重。"""
    fake = make_fake_tool(
        "fake_dump",
        ["flag{first_hit} noise flag{second_hit} again flag{first_hit}"],
    )
    llm = ScriptedLLM([tool_call("fake_dump")])

    result = await run_graph(llm, [fake])

    assert result["extracted_flags"] == ["flag{first_hit}", "flag{second_hit}"]
    assert result["verification_status"] == "l1_passed"


# --------------------------------------------------------------------------
# L1 未命中：成功但无 flag → 回到 orchestrator
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_success_without_flag_returns_to_orchestrator():
    """工具成功但没 flag → 回到 orchestrator 再想一轮，不触发 flag_capture。"""
    fake = make_fake_tool("fake_nmap", ["Found 3 open ports: 22, 80, 443"])
    llm = ScriptedLLM([
        tool_call("fake_nmap", {"payload": "10.0.0.1"}),
        AIMessage(content="攻击面枚举完毕，暂未发现 flag。"),
    ])

    result = await run_graph(llm, [fake])

    assert len(llm.calls) == 2, "无 flag 时 should_continue 应回到 orchestrator"
    assert result.get("extracted_flags", []) == []
    assert result.get("verification_status") is None
    assert "暂未发现 flag" in str(result["messages"][-1].content)


# --------------------------------------------------------------------------
# L2：错误 → reflection → 恢复 → L1 命中（穿越四个节点）
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_error_triggers_reflection_then_recovers_with_flag():
    """错误 → reflection 注入 error 场景 prompt → 重试后拿到 flag。

    这是本文件的核心用例：一次运行穿越 orchestrator → tools → reflection →
    orchestrator → tools → flag_capture 六个跳。
    """
    fake = make_fake_tool("fake_sqlmap", [
        "Error: connection refused",
        "Database dumped: flag{r3flect_then_w1n}",
    ])
    llm = ScriptedLLM([
        tool_call("fake_sqlmap", {"payload": "http://target"}),
        tool_call("fake_sqlmap", {"payload": "http://target"}),
    ])

    result = await run_graph(llm, [fake])

    # reflection 节点确实运行了：递增 retry_count 并注入反思指令
    assert result["retry_count"] == 1
    injected = injected_user_messages(result)
    assert len(injected) == 1
    assert "反思时刻" in injected[0]
    assert "第 1/3 次尝试" in injected[0]
    assert "connection refused" in injected[0], "反思 prompt 应带上原始错误信息"

    # 反思后的第二次尝试命中 flag
    assert result["extracted_flags"] == ["flag{r3flect_then_w1n}"]
    assert result["verification_status"] == "l1_passed"

    # 第二次 orchestrator 调用确实看到了注入的反思指令
    assert len(llm.calls) == 2
    second_call = "\n".join(str(m.content) for m in llm.calls[1])
    assert "反思时刻" in second_call, "反思 prompt 必须真的被送进 LLM 上下文"


@pytest.mark.asyncio
async def test_second_reflection_switches_to_stale_scenario():
    """连续失败到第二次 reflection 时，场景从 progress 切到 stale，并建议 PoC 验证。"""
    fake = make_fake_tool("fake_recon", [
        "indeterminate: no exploitable vector found",
        "indeterminate: no exploitable vector found",
    ])
    llm = ScriptedLLM([
        tool_call("fake_recon"),
        tool_call("fake_recon"),
        AIMessage(content="已穷尽当前方向。"),
    ])

    result = await run_graph(llm, [fake])

    assert result["retry_count"] == 2
    injected = injected_user_messages(result)
    assert len(injected) == 2
    # 第 1 次是 progress（retry_count 尚未达到阈值）
    assert "进展分析" in injected[0]
    # 第 2 次切换到 stale，并引导写 PoC
    assert "停滞检测" in injected[1]
    assert "第 2/3 次尝试" in injected[1]
    assert "PoC" in injected[1] or "sandbox" in injected[1].lower()

    # 全程没有 flag，图靠 LLM 给出无 tool_calls 的回复正常结束
    assert result.get("extracted_flags", []) == []
    assert len(llm.calls) == 3


# --------------------------------------------------------------------------
# L2 边界：重试上限 → END，不再 reflection
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retry_limit_terminates_instead_of_reflecting():
    """retry_count 已达上限时，错误输出直接终止而不是再次 reflection。"""
    fake = make_fake_tool("fake_exploit", ["Error: still failing"])
    llm = ScriptedLLM([tool_call("fake_exploit")])

    result = await run_graph(llm, [fake], initial_state={"retry_count": 3})

    assert len(llm.calls) == 1, "到达重试上限后不应再调用 LLM"
    assert result["retry_count"] == 3
    assert injected_user_messages(result) == [], "上限后不应再注入反思 prompt"
    assert isinstance(result["messages"][-1], ToolMessage)


@pytest.mark.asyncio
async def test_flag_wins_over_error_keyword_in_same_output():
    """输出同时含 'error' 和 flag 时，L1 优先于错误分支路由到 flag_capture。"""
    fake = make_fake_tool(
        "fake_mixed",
        ["Error: partial dump, but recovered flag{l1_before_error}"],
    )
    llm = ScriptedLLM([tool_call("fake_mixed")])

    result = await run_graph(llm, [fake])

    assert result["extracted_flags"] == ["flag{l1_before_error}"]
    assert result["verification_status"] == "l1_passed"
    assert len(llm.calls) == 1, "应走 flag_capture 分支而非 reflection"
    assert injected_user_messages(result) == []
