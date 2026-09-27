# 验证闭环 (Verification Loop) 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 CTF-ASAS 引入三级验证闭环（L1 格式验证 / L2 语义验证 / L3 PoC 重放），直接提升 flag 提取成功率和结果可信度。

**Architecture:** 不新增独立 LangGraph Node，而是增强现有 `should_continue` 条件分支 + `reflection_node` 逻辑。L1 用正则从工具输出中提取 flag 并写入 state；L2 在 reflection 中引导 LLM 做语义判断；L3 在 sandbox 中运行独立 PoC 脚本验证 payload 有效性。三级验证形成递进式闭环。

**Tech Stack:** Python 3.10+, LangGraph, Pydantic, re, pytest

**设计决策:**
- FlagExtractor 作为独立模块，可被 dispatcher.py 和 workflow.py 共用
- L1 嵌入 `should_continue`（零架构变动）
- L2 增强现有 `reflection_node`（最小改动）
- L3 复用已有 `sandbox_execute`（零新依赖）
- `AgentState` 新增 `extracted_flags` 字段存放提取结果

---

### Task 0: 创建分支 & 前置目录

**Step 1: 创建 feature 分支**

```bash
cd /Users/guoshuguang/my-project/ctfbot
git checkout -b feat/verification-loop
```

**Step 2: 创建空文件占位**

```bash
mkdir -p tests/agent
touch tests/agent/__init__.py
touch src/asas_agent/graph/verifier.py
```

**Step 3: Commit**

```bash
git add tests/agent/__init__.py src/asas_agent/graph/verifier.py
git commit -m "chore: 创建验证闭环模块骨架"
```

---

### Task 1: FlagExtractor — 多格式 Flag 正则提取器

**Files:**
- Create: `src/asas_agent/graph/verifier.py`
- Create: `tests/agent/test_verifier.py`

**Step 1: 写失败测试**

```python
# tests/agent/test_verifier.py
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
```

**Step 2: 运行测试确认失败**

```bash
cd /Users/guoshuguang/my-project/ctfbot
python -m pytest tests/agent/test_verifier.py -v
```
Expected: FAIL — `ImportError: cannot import name 'FlagExtractor'`

**Step 3: 实现 FlagExtractor**

```python
# src/asas_agent/graph/verifier.py
"""验证闭环模块：Flag 提取 + PoC 验证"""
import re
from typing import Optional


# 支持的 flag 前缀（小写匹配）
_FLAG_PREFIXES = [
    "flag",
    "ctf",
    "ctfshow",
    "hctf",
    "sctf",
    "hitcon",
    "bctf",
    "qwb",       # 强网杯
    "dasctf",
    "moectf",
    "iscc",
]

# 构建正则：(flag|ctf|ctfshow|...)\{[^}]+\}
_PREFIX_PATTERN = "|".join(re.escape(p) for p in _FLAG_PREFIXES)
_FLAG_RE = re.compile(
    rf"({_PREFIX_PATTERN})\{{([^}}]+)\}}",
    re.IGNORECASE,
)


class FlagExtractor:
    """从任意文本中提取 CTF flag。

    支持多种前缀格式，大小写不敏感，自动去重。
    """

    def __init__(self, extra_prefixes: Optional[list[str]] = None):
        if extra_prefixes:
            all_prefixes = _FLAG_PREFIXES + extra_prefixes
            prefix_pattern = "|".join(re.escape(p) for p in all_prefixes)
            self._re = re.compile(
                rf"({prefix_pattern})\{{([^}}]+)\}}",
                re.IGNORECASE,
            )
        else:
            self._re = _FLAG_RE

    def extract(self, text: str) -> list[str]:
        """从文本中提取所有 flag，返回去重后的列表。"""
        matches = self._re.findall(text)
        # findall 返回 [(prefix, content), ...]，重建完整 flag
        seen: set[str] = set()
        result: list[str] = []
        for prefix, content in matches:
            full_flag = f"{prefix}{{{content}}}"
            if full_flag not in seen:
                seen.add(full_flag)
                result.append(full_flag)
        return result

    def has_flag(self, text: str) -> bool:
        """快速检查文本中是否包含 flag。"""
        return bool(self._re.search(text))


# 模块级单例，方便全局使用
flag_extractor = FlagExtractor()
```

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/agent/test_verifier.py -v
```
Expected: 9 passed

**Step 5: Commit**

```bash
git add src/asas_agent/graph/verifier.py tests/agent/test_verifier.py
git commit -m "feat(verify): FlagExtractor 多格式flag正则提取器，支持10+前缀"
```

---

### Task 2: AgentState 新增 extracted_flags 字段

**Files:**
- Modify: `src/asas_agent/graph/state.py`
- Create: `tests/agent/test_state.py`

**Step 1: 写失败测试**

```python
# tests/agent/test_state.py
import pytest
from src.asas_agent.graph.state import AgentState


def test_extracted_flags_default():
    """extracted_flags 默认为空列表"""
    state = AgentState(messages=[])
    assert state.get("extracted_flags", []) == []


def test_verification_status_default():
    """verification_status 默认为 None"""
    state = AgentState(messages=[])
    assert state.get("verification_status") is None
```

**Step 2: 运行测试确认行为**

```bash
python -m pytest tests/agent/test_state.py -v
```

**Step 3: 修改 state.py — 新增验证相关字段**

在 `src/asas_agent/graph/state.py` 中，完整替换为：

```python
from langgraph.graph import MessagesState
from typing import Optional, Any, Dict, List


class AgentState(MessagesState):
    """v2.0 ReAct Agent State - inherits messages from MessagesState"""
    # v2 fields (platform context)
    platform_url: Optional[str]
    platform_token: Optional[str]
    challenge_id: Optional[str]
    
    # v3 multi-agent fields
    challenges: Optional[list]  # List of challenge objects from platform
    agent_results: Optional[Dict[str, Any]]  # {challenge_id: AgentResult}
    fact_store: Dict[str, Dict[str, Any]] = {
        "recon": {}, "web": {}, "crypto": {}, "reverse": {}, "common": {}
    }
    current_agent: Optional[str]
    retry_count: int = 0  # v4 Reflection loop counter
    
    # v5 verification loop fields
    extracted_flags: List[str] = []              # 已提取的 flag 列表
    verification_status: Optional[str] = None    # None / "l1_passed" / "l2_needs_poc" / "l3_verified" / "failed"
    poc_attempts: int = 0                        # PoC 验证尝试次数
    
    # v1 compatibility fields (will be deprecated)
    user_input: Optional[str]
    task_understanding: Optional[str]
    planned_tool: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    final_answer: Optional[str]
    error: Optional[str]
    task_history: Optional[list]
    pending_tasks: Optional[list]
```

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/agent/test_state.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add src/asas_agent/graph/state.py tests/agent/test_state.py
git commit -m "feat(state): 新增 extracted_flags/verification_status/poc_attempts 字段"
```

---

### Task 3: 增强 should_continue — L1 Flag 格式验证

**Files:**
- Modify: `src/asas_agent/graph/workflow.py:488-517`
- Create: `tests/agent/test_should_continue.py`

**Step 1: 写测试**

```python
# tests/agent/test_should_continue.py
import pytest
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from src.asas_agent.graph.verifier import flag_extractor


class TestShouldContinueL1:
    """测试 L1 flag 格式验证的 FlagExtractor 行为"""

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
```

**Step 2: 运行测试确认通过**

```bash
python -m pytest tests/agent/test_should_continue.py -v
```
Expected: PASS

**Step 3: 修改 workflow.py**

在 `src/asas_agent/graph/workflow.py` 的 `create_orchestrator_graph` 函数中：

**3a.** 在 `reflection_node` 之后、`workflow.add_edge(START, "orchestrator")` 之前，新增 `flag_capture` 节点（约 L484 之后插入）：

```python
    def flag_capture_node(state: AgentState):
        """捕获工具输出中的 flag 并更新 state"""
        from .verifier import flag_extractor
        
        messages = state["messages"]
        existing_flags = list(state.get("extracted_flags", []))
        
        # 扫描最近的消息寻找 flag
        for msg in reversed(messages[-5:]):
            content = str(getattr(msg, "content", ""))
            found = flag_extractor.extract(content)
            for f in found:
                if f not in existing_flags:
                    existing_flags.append(f)
        
        if existing_flags:
            print(f"🏁 [FlagCapture] 已捕获 flags: {existing_flags}")
        
        return {
            "extracted_flags": existing_flags,
            "verification_status": "l1_passed" if existing_flags else None,
        }
    
    workflow.add_node("flag_capture", flag_capture_node)
```

**3b.** 替换 `should_continue` 函数（L488-511）为：

```python
    def should_continue(state: AgentState):
        from .verifier import flag_extractor
        
        messages = state["messages"]
        last_message = messages[-1]
        
        # 1. AI message with tool calls → route to tools
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            print(f"DEBUG [should_continue]: AIMessage with tool_calls -> 'tools'")
            return "tools"
            
        # 2. Tool output → L1 验证 + 条件路由
        if isinstance(last_message, ToolMessage):
            content = str(last_message.content)
            
            # === L1: Flag 格式验证 ===
            if flag_extractor.has_flag(content):
                print(f"🚩 [L1 验证通过] 工具输出中发现 flag")
                return "flag_capture"
            
            # === 错误检测 → reflection ===
            content_lower = content.lower()
            if "error" in content_lower or "failed" in content_lower or "indeterminate" in content_lower:
                retries = state.get("retry_count", 0)
                if retries < 3:
                    print(f"DEBUG [should_continue]: ToolMessage error -> 'reflection'")
                    return "reflection"
                else:
                    print(f"DEBUG [should_continue]: Retry limit reached -> END")
                    return END
            
            # === 成功但无 flag → 继续 orchestrator ===
            print(f"DEBUG [should_continue]: ToolMessage success (no flag) -> 'orchestrator'")
            return "orchestrator"
            
        print(f"DEBUG [should_continue]: Fallthrough -> END")
        return END
```

**3c.** 替换原来的 `add_conditional_edges` 和 `add_edge`（L513-516）为：

```python
    workflow.add_conditional_edges("orchestrator", should_continue, ["tools", "orchestrator", "flag_capture", END])
    workflow.add_conditional_edges("tools", should_continue, ["orchestrator", "reflection", "flag_capture", END])
    workflow.add_edge("reflection", "orchestrator")
    workflow.add_edge("flag_capture", END)
```

**Step 4: 运行测试确认无回归**

```bash
python -m pytest tests/ -v --ignore=tests/distributed --ignore=tests/ui -x
```
Expected: 全部 PASS

**Step 5: Commit**

```bash
git add src/asas_agent/graph/workflow.py tests/agent/test_should_continue.py
git commit -m "feat(verify): L1 flag格式验证嵌入should_continue + flag_capture节点"
```

---

### Task 4: 增强 reflection_node — L2 语义验证

**Files:**
- Modify: `src/asas_agent/graph/workflow.py:459-482`
- Modify: `src/asas_agent/graph/verifier.py` (追加 `build_reflection_prompt`)
- Create: `tests/agent/test_reflection.py`

**Step 1: 写失败测试**

```python
# tests/agent/test_reflection.py
import pytest
from src.asas_agent.graph.verifier import build_reflection_prompt


class TestReflectionPrompts:

    def test_error_scenario_prompt(self):
        """错误场景 → prompt 包含重试次数和错误信息"""
        prompt = build_reflection_prompt(
            retry_count=0,
            content="sqlmap: connection timed out",
            scenario="error"
        )
        assert "第 1/3 次尝试" in prompt
        assert "connection timed out" in prompt
        assert "检查参数" in prompt

    def test_progress_scenario_prompt(self):
        """有进展但无 flag → prompt 要求生成下一步"""
        prompt = build_reflection_prompt(
            retry_count=0,
            content="Found 3 databases: information_schema, mysql, ctf_challenge",
            scenario="progress"
        )
        assert "继续" in prompt or "下一步" in prompt

    def test_stale_scenario_prompt(self):
        """多次成功但无 flag → prompt 建议 PoC 验证"""
        prompt = build_reflection_prompt(
            retry_count=2,
            content="Dumped table: users (admin, password123)",
            scenario="stale"
        )
        assert "PoC" in prompt or "sandbox" in prompt.lower()

    def test_retry_count_increments(self):
        """重试次数正确递增"""
        prompt = build_reflection_prompt(retry_count=1, content="error", scenario="error")
        assert "第 2/3 次尝试" in prompt
```

**Step 2: 运行测试确认失败**

```bash
python -m pytest tests/agent/test_reflection.py -v
```
Expected: FAIL — `cannot import name 'build_reflection_prompt'`

**Step 3: 在 verifier.py 追加 build_reflection_prompt**

在 `src/asas_agent/graph/verifier.py` 末尾追加：

```python
def build_reflection_prompt(retry_count: int, content: str, scenario: str) -> str:
    """构造不同场景下的 reflection prompt。
    
    Args:
        retry_count: 当前重试次数（从 0 开始）
        content: 上一步工具输出内容（截断后）
        scenario: "error" / "progress" / "stale"
    
    Returns:
        引导 LLM 反思的 prompt 字符串
    """
    current_attempt = retry_count + 1
    
    if scenario == "error":
        return (
            f"反思时刻 (第 {current_attempt}/3 次尝试)：\n"
            f"上一步工具调用返回了错误。\n"
            f"错误信息: {content[:500]}\n\n"
            "请分析失败原因，并生成一个新的策略。你可以尝试：\n"
            "1. 检查参数是否正确（URL、端口、路径）。\n"
            "2. 换一个工具或方法。\n"
            "3. 使用 `memory_query` 查找类似问题的解决办法。\n"
            "4. 使用 `kali_exec` 手工执行命令探查。\n\n"
            "请直接调用工具，不要只是分析。"
        )
    
    elif scenario == "progress":
        return (
            f"进展分析 (第 {current_attempt}/3 次尝试)：\n"
            f"上一步工具调用成功返回了结果，但尚未找到 flag。\n"
            f"工具输出: {content[:500]}\n\n"
            "请分析当前进展，并决定下一步：\n"
            "1. 如果发现了数据库/表/文件 → 继续深入提取数据。\n"
            "2. 如果输出中有疑似 flag 的编码内容 → 尝试解码。\n"
            "3. 如果当前攻击面已穷尽 → 切换到其他方向。\n\n"
            "目标：找到 flag{...} 格式的字符串。请直接调用工具。"
        )
    
    elif scenario == "stale":
        return (
            f"停滞检测 (第 {current_attempt}/3 次尝试)：\n"
            f"已多次成功执行工具但仍未找到 flag。\n"
            f"最近输出: {content[:500]}\n\n"
            "建议采取以下措施之一：\n"
            "1. 编写一个独立的 PoC 脚本验证之前的发现。\n"
            "   使用 `sandbox_execute(code='import requests; ...')` 在沙箱中运行。\n"
            "2. 回顾之前的所有发现，检查是否遗漏了关键信息。\n"
            "3. 使用 `search_writeups` 搜索类似题目的 WriteUp。\n\n"
            "请直接调用工具，不要重复之前已失败的尝试。"
        )
    
    # 兜底
    return (
        f"第 {current_attempt}/3 次尝试：\n"
        f"当前输出: {content[:300]}\n"
        "请决定下一步行动并调用工具。"
    )
```

然后修改 `workflow.py` 中的 `reflection_node`（L459-482），替换为：

```python
    # Reflection Node Logic
    def reflection_node(state: AgentState):
        from langchain_core.messages import SystemMessage, HumanMessage
        from .verifier import build_reflection_prompt, flag_extractor
        
        messages = state["messages"]
        last_tool_msg = messages[-1]
        content = str(last_tool_msg.content) if hasattr(last_tool_msg, "content") else ""
        
        # Increment retry count
        current_retries = state.get("retry_count", 0) + 1
        
        # 判断场景
        content_lower = content.lower()
        if "error" in content_lower or "failed" in content_lower:
            scenario = "error"
        elif current_retries >= 2 and not flag_extractor.has_flag(content):
            scenario = "stale"
        else:
            scenario = "progress"
        
        reflection_prompt = build_reflection_prompt(
            current_retries - 1, content, scenario
        )
        
        return {
            "messages": [HumanMessage(content=reflection_prompt)],
            "retry_count": current_retries
        }
```

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/agent/test_reflection.py -v
python -m pytest tests/ -v --ignore=tests/distributed --ignore=tests/ui -x
```
Expected: 全部 PASS

**Step 5: Commit**

```bash
git add src/asas_agent/graph/verifier.py src/asas_agent/graph/workflow.py tests/agent/test_reflection.py
git commit -m "feat(verify): L2 语义验证 — 三场景 reflection prompt + 增强 reflection_node"
```

---

### Task 5: 统一 dispatcher.py 的 flag 提取

**Files:**
- Modify: `src/asas_agent/graph/dispatcher.py:165-177`
- Create: `tests/agent/test_dispatcher_verify.py`

**Step 1: 写测试**

```python
# tests/agent/test_dispatcher_verify.py
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
```

**Step 2: 运行测试确认通过**

```bash
python -m pytest tests/agent/test_dispatcher_verify.py -v
```
Expected: PASS

**Step 3: 修改 dispatcher.py**

在 `src/asas_agent/graph/dispatcher.py` 第 165-177 行，将：

```python
        # 7. Post-process to find Flag and Facts
        flag = None
        extracted_facts = {}
        import re
        
        # Extract Flag
        flag_match = re.search(r"flag\{.*?\}", reasoning, re.IGNORECASE)
        if flag_match:
            flag = flag_match.group(0)
            status = "success"
        else:
            status = "indeterminate"
```

替换为：

```python
        # 7. Post-process to find Flag and Facts
        from .verifier import flag_extractor
        
        extracted_facts = {}
        
        # Extract Flag (复用统一的 FlagExtractor)
        flags = flag_extractor.extract(reasoning)
        if flags:
            flag = flags[0]  # 取第一个匹配
            status = "success"
        else:
            flag = None
            status = "indeterminate"
```

**Step 4: 运行测试确认无回归**

```bash
python -m pytest tests/ -v --ignore=tests/distributed --ignore=tests/ui -x
```
Expected: 全部 PASS

**Step 5: Commit**

```bash
git add src/asas_agent/graph/dispatcher.py tests/agent/test_dispatcher_verify.py
git commit -m "refactor(dispatcher): 统一使用 FlagExtractor 替代硬编码正则"
```

---

### Task 6: 集成测试 — 验证闭环端到端

**Files:**
- Create: `tests/agent/test_verification_e2e.py`

**Step 1: 写集成测试**

```python
# tests/agent/test_verification_e2e.py
"""验证闭环端到端测试"""
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
        ]
        for text, expected in cases:
            assert extractor.extract(text) == expected, f"Failed: {text}"
```

**Step 2: 运行测试确认通过**

```bash
python -m pytest tests/agent/test_verification_e2e.py -v
```
Expected: 6 passed

**Step 3: 无需额外实现**

**Step 4: 全量测试**

```bash
python -m pytest tests/ -v --ignore=tests/distributed --ignore=tests/ui
```
Expected: 全部 PASS

**Step 5: Commit**

```bash
git add tests/agent/test_verification_e2e.py
git commit -m "test(verify): 验证闭环 L1/L2 端到端集成测试"
```

---

## 下一步

Phase 1 完成后，继续实施：
- **Phase 2**: 发现黑板增强（`docs/plans/2026-09-26-strix-phase2-blackboard.md`）
- **Phase 3**: CTF 基准测试集（`docs/plans/2026-09-26-strix-phase3-benchmark.md`）
