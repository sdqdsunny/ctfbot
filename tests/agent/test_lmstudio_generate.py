"""LMStudioLLM._generate 的请求组装与工具调用解析测试。

为什么单独写这个文件：``test_llm_factory.py`` 只断言 ``create_llm`` 选对了类
（``isinstance(llm, LMStudioLLM)``），``_generate`` 此前**零覆盖**。而它正好是
一次交付审计里发现问题的位置——那段未提交的改动捆了三件事：

1. 一段显式"绕过对齐拒绝"的越狱提示词（已删）
2. 一段硬编码 ``192.168.1.1`` 的 few-shot 伪造对话，每轮都注入（已删）
3. ``<tool_call>`` / ``[TOOL_REQUEST]`` 文本格式的解析（保留，本地模型靠它才能调工具）

下面 ``test_request_contains_only_real_conversation`` 等用例的作用就是把 1、2
钉住：一旦有人再把伪造轮次或越狱文案塞进 payload，这里会立刻红，而不是等到
分发出的产物里被人翻出来。

跑法（需要 PYTHONPATH=src，本项目未装 editable 包）::

    PYTHONPATH=src .venv/bin/python -m pytest tests/agent/test_lmstudio_generate.py -v
"""
import json
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from asas_agent.llm.factory import _REQUEST_TIMEOUT_S, LMStudioLLM


def _llm() -> LMStudioLLM:
    return LMStudioLLM(base_url="http://localhost:1234/v1", model_name="test-model")


def _respond(content="", tool_calls=None):
    """构造一个假的 requests.post 返回值，让 _generate 走完正常分支。"""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    message = {"content": content}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    resp.json.return_value = {"choices": [{"message": message}]}
    return resp


def _sent_payload(mock_post) -> dict:
    """取出真正发出去的 payload（关键字或位置传参都兜住）。"""
    if mock_post.call_args.kwargs.get("json") is not None:
        return mock_post.call_args.kwargs["json"]
    return mock_post.call_args.args[1]


# --------------------------------------------------------------------------
# 请求组装：只许出现真实对话
# --------------------------------------------------------------------------

def test_request_contains_only_real_conversation():
    """发出去的 messages 必须**只有**真实对话，不许有任何伪造轮次。

    这是针对"硬编码 192.168.1.1 的 few-shot"那条改动的回归锁：那段代码会往每次
    请求前面插 4 条伪造消息（含 2 条带 tool_calls 的 assistant 和 1 条假工具输出）。
    除了污染上下文，它还会把模型往那个内网 IP 上引——真实目标不是它时，
    模型可能把工具参数写成 192.168.1.1。
    """
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond("ok")
        _llm()._generate([
            SystemMessage(content="SYS-PROMPT"),
            HumanMessage(content="scan 10.0.0.5"),
        ])

    msgs = _sent_payload(mock_post)["messages"]

    # 系统提示被合并进首条用户消息，所以真实对话只剩 1 条
    assert len(msgs) == 1, f"除真实对话外还有额外消息被注入: {msgs}"
    # 整份 payload 里不该出现任何被伪造的目标
    assert "192.168.1.1" not in json.dumps(_sent_payload(mock_post))


def test_no_jailbreak_text_is_injected():
    """payload 里不许再出现那段越狱文案。

    删掉它不只是"少一段字符串"：代码里那句 ``# Add a jailbreak prompt to bypass
    alignment rejections`` 的注释本身就是分发出产品时最直接的声誉证据。
    """
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond("ok")
        _llm()._generate([
            SystemMessage(content="SYS-PROMPT"),
            HumanMessage(content="scan 10.0.0.5"),
        ])

    blob = json.dumps(_sent_payload(mock_post)).lower()
    for forbidden in ("jailbreak", "no moral warnings", "headless automation", "bypass"):
        assert forbidden not in blob, f"payload 里仍有越狱痕迹: {forbidden!r}"


def test_system_prompt_merged_into_first_user_message():
    """系统提示仍按原设计合并进首条用户消息，且带 USER COMMAND: 分隔标记。"""
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond("ok")
        _llm()._generate([
            SystemMessage(content="SYS-PROMPT"),
            HumanMessage(content="scan 10.0.0.5"),
        ])

    content = _sent_payload(mock_post)["messages"][0]["content"]
    assert content == "SYS-PROMPT\n\nUSER COMMAND: scan 10.0.0.5"


def test_timeout_comes_from_the_named_constant():
    """超时取自具名常量，不再是埋在调用里的魔法数字。"""
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond("ok")
        _llm()._generate([HumanMessage(content="hi")])

    assert mock_post.call_args.kwargs["timeout"] == _REQUEST_TIMEOUT_S


# --------------------------------------------------------------------------
# 工具调用解析：原生格式（原有行为，防被 else 分支遮蔽）
# --------------------------------------------------------------------------

def test_native_tool_calls_are_parsed():
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond(
            content="",
            tool_calls=[{
                "id": "call_abc",
                "type": "function",
                "function": {"name": "kali_nmap", "arguments": json.dumps({"target": "10.0.0.5"})},
            }],
        )
        result = _llm()._generate([HumanMessage(content="scan")])

    calls = result.generations[0].message.tool_calls
    assert calls == [{
        "name": "kali_nmap",
        "args": {"target": "10.0.0.5"},
        "id": "call_abc",
        "type": "tool_call",
    }]


# --------------------------------------------------------------------------
# 工具调用解析：文本格式（本地模型的常见输出，本次保留的功能）
# --------------------------------------------------------------------------

def test_tool_call_text_block_is_parsed_and_stripped():
    """``<tool_call>`` 文本块被解析成 tool_calls，且从正文里剔除。

    LM Studio 里的本地模型经常不返回原生 tool_calls，而是把调用当普通文本吐出来。
    不解析就等于这条路径下模型"不能调工具"。
    """
    raw = (
        "Let me scan that host.\n"
        "<tool_call>\n"
        "<function=kali_nmap>\n"
        "<parameter=target>10.0.0.5</parameter>\n"
        "<parameter=args>-p-</parameter>\n"
        "</function>\n"
        "</tool_call>"
    )
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond(content=raw)
        message = _llm()._generate([HumanMessage(content="scan")]).generations[0].message

    assert len(message.tool_calls) == 1
    call = message.tool_calls[0]
    assert call["name"] == "kali_nmap"
    assert call["args"] == {"target": "10.0.0.5", "args": "-p-"}
    # 解析过的块要从正文里消失，否则会被当成模型的话术再回灌一轮
    assert "<tool_call>" not in message.content
    assert message.content == "Let me scan that host."


def test_tool_request_block_is_parsed_and_stripped():
    """``[TOOL_REQUEST]{json}[END_TOOL_REQUEST]`` 走 JSON 解析，参数保留原始类型。"""
    raw = '[TOOL_REQUEST]{"name": "kali_sqlmap", "arguments": {"url": "http://t/x", "level": 3}}[END_TOOL_REQUEST]'
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond(content=raw)
        message = _llm()._generate([HumanMessage(content="sqli")]).generations[0].message

    assert len(message.tool_calls) == 1
    assert message.tool_calls[0]["name"] == "kali_sqlmap"
    # 走 json.loads 的这条路径类型是对的——注意上面 <tool_call> 那条只会给字符串
    assert message.tool_calls[0]["args"] == {"url": "http://t/x", "level": 3}
    assert "[TOOL_REQUEST]" not in message.content


def test_malformed_tool_request_does_not_crash():
    """坏 JSON 只跳过，不能让整个 agent 崩掉——交付产物里崩一次就是一次白跑。"""
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.return_value = _respond(content="[TOOL_REQUEST]{not json}[END_TOOL_REQUEST]")
        message = _llm()._generate([HumanMessage(content="x")]).generations[0].message

    assert message.tool_calls == []


# --------------------------------------------------------------------------
# 错误路径：连接不上要退化成消息，而不是抛异常
# --------------------------------------------------------------------------

def test_connection_failure_degrades_to_message():
    with patch("asas_agent.llm.factory.requests.post") as mock_post:
        mock_post.side_effect = ConnectionError("connection refused")
        message = _llm()._generate([HumanMessage(content="x")]).generations[0].message

    assert isinstance(message, AIMessage)
    assert "Error connecting to LM Studio" in message.content
