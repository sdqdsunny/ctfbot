# ASAS Agent MVP 设计方案

**创建日期:** 2026-02-07  
**版本:** 1.0  
**状态:** 设计完成,待实施

---

## 1. 项目目标

实现 CTF-ASAS 系统的**任务编排层 (Agent)**,作为独立服务通过 MCP 协议调用现有工具,验证端到端的自动解题流程。

### MVP 范围

- **核心场景:** 单步任务 - 用户输入 "解码这段 Base64",系统理解意图 → 调用工具 → 返回结果
- **架构验证:** 独立 Agent 服务 + MCP 协议通信
- **LLM 集成:** 支持 Mock 和真实 LLM 两种模式

---

## 2. 总体架构

### 2.1 系统分层

```
┌─────────────────────────────────────┐
│   用户接口 (CLI/API)                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   asas-agent (决策层)                │
│   - LangGraph 状态机                 │
│   - LLM Provider (Mock/Real)        │
│   - 任务理解与规划                    │
└──────────────┬──────────────────────┘
               │ MCP Protocol
┌──────────────▼──────────────────────┐
│   asas-core-mcp (能力层)             │
│   - recon_scan                      │
│   - crypto_decode                   │
│   - misc_identify_file              │
│   - reverse_extract_strings         │
└─────────────────────────────────────┘
```

### 2.2 项目结构

```
ctfbot/
├── src/
│   ├── asas_mcp/          # 现有的 MCP 工具服务
│   └── asas_agent/        # 新增的 Agent 编排服务
│       ├── __init__.py
│       ├── __main__.py    # CLI 入口
│       ├── graph/         # LangGraph 状态机
│       │   ├── __init__.py
│       │   ├── state.py   # 状态定义
│       │   └── nodes.py   # 节点函数
│       ├── llm/           # LLM 抽象层
│       │   ├── __init__.py
│       │   ├── base.py    # 抽象基类
│       │   ├── mock.py    # Mock LLM
│       │   └── claude.py  # Claude 集成
│       ├── mcp_client/    # MCP 协议客户端
│       │   ├── __init__.py
│       │   └── client.py
│       └── models/        # 数据模型
│           └── __init__.py
├── tests/
│   └── agent/
│       ├── test_graph.py
│       ├── test_llm.py
│       └── test_integration.py
```

---

## 3. LangGraph 状态机设计

### 3.1 状态流程

```
START
  ↓
UNDERSTAND_TASK (理解用户意图)
  ↓
PLAN_ACTIONS (规划需要调用的工具)
  ↓
EXECUTE_TOOL (调用 MCP 工具)
  ↓
FORMAT_RESULT (格式化结果)
  ↓
END
```

### 3.2 状态定义

```python
from typing import TypedDict

class AgentState(TypedDict):
    """Agent 状态"""
    user_input: str              # 用户输入
    task_understanding: str      # 任务理解
    planned_tool: str           # 计划使用的工具
    tool_args: dict             # 工具参数
    tool_result: str            # 工具执行结果
    final_answer: str           # 最终答案
    error: str | None           # 错误信息
```

### 3.3 核心节点函数

```python
def understand_task(state: AgentState) -> AgentState:
    """使用 LLM 理解用户意图"""
    # Mock 模式: 简单规则匹配
    # Real 模式: 调用 LLM 分析意图
    pass

def plan_actions(state: AgentState) -> AgentState:
    """规划需要调用的工具"""
    # 根据任务理解,选择合适的工具和参数
    pass

def execute_tool(state: AgentState) -> AgentState:
    """通过 MCP 客户端调用工具"""
    # 连接 asas-core-mcp,执行工具调用
    pass

def format_result(state: AgentState) -> AgentState:
    """格式化最终结果"""
    # 将工具结果转换为用户友好的输出
    pass
```

---

## 4. LLM 抽象层

### 4.1 接口设计

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProvider(ABC):
    """LLM 提供者抽象基类"""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """发送消息并获取响应"""
        pass
```

### 4.2 Mock LLM 实现

```python
class MockLLM(LLMProvider):
    """Mock LLM - 用于开发和测试"""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        user_msg = messages[-1]["content"].lower()
        
        # 简单的规则匹配
        if "base64" in user_msg or "解码" in user_msg:
            return "crypto_decode"
        elif "扫描" in user_msg or "scan" in user_msg:
            return "recon_scan"
        elif "文件" in user_msg or "file" in user_msg:
            return "misc_identify_file"
        elif "字符串" in user_msg or "string" in user_msg:
            return "reverse_extract_strings"
        
        return "unknown"
```

### 4.3 Claude LLM 实现

```python
from anthropic import Anthropic

class ClaudeLLM(LLMProvider):
    """Claude API 集成"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=messages
        )
        return response.content[0].text
```

---

## 5. MCP 客户端

### 5.1 客户端实现

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPToolClient:
    """MCP 工具调用客户端"""
    
    def __init__(self, server_command: str = "python", 
                 server_args: list = ["-m", "asas_mcp"]):
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args
        )
    
    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """调用 MCP Server 的工具"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text
    
    async def list_tools(self) -> list:
        """列出可用工具"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return tools.tools
```

---

## 6. CLI 工具

### 6.1 使用示例

```bash
# Mock 模式测试
python -m asas_agent "解码这段 Base64: SGVsbG8gV29ybGQ="

# 真实 LLM 模式
python -m asas_agent --llm=claude "解码这段 Base64: SGVsbG8gV29ybGQ="

# 指定 API Key
python -m asas_agent --llm=claude --api-key=sk-xxx "解码这段 Base64: SGVsbG8gV29ybGQ="
```

### 6.2 预期输出

```
🤖 ASAS Agent (Mock Mode)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 理解任务: 用户需要解码 Base64 编码的字符串
🔧 规划工具: crypto_decode
⚙️  执行工具: crypto_decode(content="SGVsbG8gV29ybGQ=", method="base64")
✅ 工具结果: Hello World

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 最终答案: Hello World
```

---

## 7. 测试策略

### 7.1 单元测试

- `test_llm.py`: 测试 Mock 和 Claude LLM Provider
- `test_graph.py`: 测试状态机各节点函数
- `test_mcp_client.py`: 测试 MCP 客户端 (使用 mock server)

### 7.2 集成测试

- `test_integration.py`: 端到端测试
  - Mock 模式: "解码 SGVsbG8gV29ybGQ=" → "Hello World"
  - Real 模式: 使用真实 LLM 和 MCP Server

### 7.3 测试覆盖率目标

- 单元测试覆盖率: ≥ 80%
- 集成测试: 至少 3 个端到端场景

---

## 8. 技术栈

| 组件 | 技术选型 |
|------|---------|
| Agent 框架 | LangGraph |
| LLM API | Anthropic Claude 3.5 Sonnet |
| MCP 协议 | mcp Python SDK |
| 异步框架 | asyncio |
| CLI 框架 | argparse / click |
| 测试框架 | pytest + pytest-asyncio |

---

## 9. 依赖清单

```toml
[tool.poetry.dependencies]
python = "^3.10"
langgraph = "^0.2.0"
anthropic = "^0.40.0"
mcp = "^1.26.0"
click = "^8.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
```

---

## 10. 交付物

### 10.1 代码实现

- ✅ `asas-agent` 服务完整代码
- ✅ LangGraph 状态机实现
- ✅ LLM 抽象层 (Mock + Claude)
- ✅ MCP 客户端
- ✅ CLI 工具

### 10.2 文档

- ✅ 架构设计文档 (本文档)
- ✅ 使用说明 (README)
- ✅ 测试报告

### 10.3 成功标准

- ✅ Mock 模式下能够正确识别并调用 `crypto_decode` 工具
- ✅ 真实 LLM 模式下能够理解自然语言并完成解码任务
- ✅ 所有单元测试和集成测试通过
- ✅ CLI 工具可用且输出清晰

---

## 11. 后续扩展方向

MVP 验证成功后,可以扩展:

1. **多步任务**: 支持递归任务拆解 (如多层编码)
2. **混合工具**: 跨类型工具调用 (如 scan → identify → decode)
3. **事实仓库**: 存储中间结果和推理过程
4. **回溯机制**: 当一条路径失败时自动尝试其他方案
5. **平台集成**: 对接 BUUCTF/CTFd 自动取题和提交

---

## 12. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| MCP 协议通信不稳定 | 高 | 添加重试机制和超时控制 |
| LLM 理解错误 | 中 | Mock 模式先验证流程,逐步优化 Prompt |
| 异步调用复杂度 | 中 | 充分的单元测试,使用 pytest-asyncio |
| API 调用成本 | 低 | 默认使用 Mock 模式,仅集成测试用真实 LLM |
